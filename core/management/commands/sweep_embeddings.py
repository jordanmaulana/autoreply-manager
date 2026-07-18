from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from core.models import Knowledge
from core.rag.runner import STALE_AFTER, start_embedding_job


class Command(BaseCommand):
    help = (
        "Re-drive knowledge stuck in PROCESSING/PENDING after a crash or restart. "
        "The daemon-thread embedding path has no queue, so a process death mid-embed "
        "leaves the row wedged. Run every few minutes via cron, like refresh_tokens."
    )

    def handle(self, *args, **options):
        cutoff = timezone.now() - STALE_AFTER
        stuck = Knowledge.objects.filter(
            Q(status=Knowledge.Status.PROCESSING, embedding_started_on__lt=cutoff)
            | Q(status=Knowledge.Status.PROCESSING, embedding_started_on__isnull=True)
            | Q(status=Knowledge.Status.PENDING, updated_on__lt=cutoff)  # thread never spawned
        ).values_list("id", flat=True)

        redriven = 0
        for knowledge_id in list(stuck):
            # start_embedding_job re-claims the stale row (atomic conditional update)
            # and spawns a fresh embedding thread.
            if start_embedding_job(knowledge_id):
                redriven += 1
        self.stdout.write(f"redriven={redriven}")
