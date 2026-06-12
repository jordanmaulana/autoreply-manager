import hashlib
import logging
import threading
from datetime import timedelta

from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from core.models import Knowledge, KnowledgeChunk
from core.rag.chunking import chunk_text
from core.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=15)


def description_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def start_embedding_job(knowledge_id: str) -> bool:
    """Atomically claim the knowledge and embed it in a daemon thread.

    Returns False when another worker already owns a fresh PROCESSING claim.
    """
    now = timezone.now()
    claimed = Knowledge.objects.filter(
        Q(id=knowledge_id)
        & (
            ~Q(status=Knowledge.Status.PROCESSING)
            | Q(embedding_started_on__lt=now - STALE_AFTER)
            | Q(embedding_started_on__isnull=True)
        )
    ).update(
        status=Knowledge.Status.PROCESSING,
        embedding_started_on=now,
        status_error="",
    )
    if not claimed:
        return False
    threading.Thread(target=_run, args=(knowledge_id,), daemon=True).start()
    return True


def _run(knowledge_id: str):
    close_old_connections()
    try:
        knowledge = Knowledge.objects.get(id=knowledge_id)
        chunks = chunk_text(knowledge.description)
        if not chunks:
            raise ValueError("Description produced no chunks; add some text.")
        vectors = embed_texts([c.text for c in chunks])
        with transaction.atomic():
            KnowledgeChunk.objects.filter(knowledge=knowledge).delete()
            KnowledgeChunk.objects.bulk_create(
                [
                    KnowledgeChunk(
                        knowledge=knowledge,
                        actor=knowledge.actor,
                        seq=chunk.seq,
                        text=chunk.text,
                        token_count=chunk.token_count,
                        embedding=vector,
                    )
                    for chunk, vector in zip(chunks, vectors, strict=True)
                ],
                batch_size=500,
            )
            Knowledge.objects.filter(id=knowledge_id).update(
                status=Knowledge.Status.READY,
                chunk_count=len(chunks),
                description_sha256=description_hash(knowledge.description),
                embedded_on=timezone.now(),
                status_error="",
            )
        logger.info("embedded knowledge %s (%d chunks)", knowledge_id, len(chunks))
    except Exception as exc:
        logger.exception("embedding failed for knowledge %s", knowledge_id)
        Knowledge.objects.filter(id=knowledge_id).update(
            status=Knowledge.Status.FAILED, status_error=str(exc)[:2000]
        )
    finally:
        close_old_connections()
