import logging

from django.conf import settings
from pgvector.django import CosineDistance

from core.models import Knowledge, KnowledgeChunk, SocialAccount
from core.rag.embeddings import embed_query, get_client

logger = logging.getLogger(__name__)

TOP_K = 5
MAX_DISTANCE = 0.6
REPLY_CHAR_LIMITS = {
    SocialAccount.Platform.INSTAGRAM: 800,
    SocialAccount.Platform.WHATSAPP: 3000,
    SocialAccount.Platform.THREADS: 480,
}

SYSTEM_PROMPT = """\
You are the auto-reply assistant for {username} on {platform}.
Answer ONLY using the knowledge below. If the answer is not in the knowledge, \
say you don't know and offer to pass the question to a human.
Reply in the same language the user wrote in. Plain text only, no markdown.
Keep the reply under {char_limit} characters.
{persona}

<knowledge>
{knowledge}
</knowledge>"""


class SkipReply(Exception):
    """Raised when no reply should be generated; message becomes the skip reason."""


def retrieve_chunks(knowledge: Knowledge, query: str):
    qvec = embed_query(query)
    chunks = (
        KnowledgeChunk.objects.filter(knowledge=knowledge)
        .annotate(distance=CosineDistance("embedding", qvec))
        .order_by("distance")[:TOP_K]
    )
    return [c for c in chunks if c.distance <= MAX_DISTANCE]


def generate_reply(account: SocialAccount, inbound_text: str) -> tuple[str, list[dict]]:
    knowledge = account.knowledge
    if not knowledge:
        raise SkipReply("No knowledge linked to this account.")
    if knowledge.status != Knowledge.Status.READY:
        raise SkipReply(f"Knowledge is not ready (status: {knowledge.status}).")

    chunks = retrieve_chunks(knowledge, inbound_text)
    char_limit = REPLY_CHAR_LIMITS[account.platform]
    system = SYSTEM_PROMPT.format(
        username=account.username or account.platform_user_id,
        platform=account.get_platform_display(),
        char_limit=char_limit,
        persona=knowledge.persona,
        knowledge="\n\n---\n\n".join(c.text for c in chunks)
        or "(no relevant knowledge found for this question)",
    )
    response = get_client().chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        temperature=0.4,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": inbound_text},
        ],
    )
    reply = (response.choices[0].message.content or "").strip()[:char_limit]
    if not reply:
        raise SkipReply("Model returned an empty reply.")
    retrieved = [
        {"chunk_id": c.id, "seq": c.seq, "score": round(float(c.distance), 4)} for c in chunks
    ]
    return reply, retrieved
