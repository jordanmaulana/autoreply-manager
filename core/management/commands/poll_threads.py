import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from core.models import SocialAccount
from core.rag.inbound import handle_inbound
from core.social import threads

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Poll Threads accounts for new replies to the user's posts and auto-reply. "
        "Threads has no reply webhooks at MVP scope; run this as a separate process."
    )

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit.")

    def handle(self, *args, **options):
        while True:
            self.poll_all()
            if options["once"]:
                return
            time.sleep(settings.THREADS_POLL_SECONDS)

    def poll_all(self):
        close_old_connections()
        accounts = SocialAccount.objects.filter(
            platform=SocialAccount.Platform.THREADS,
            status=SocialAccount.Status.CONNECTED,
            auto_reply_enabled=True,
        ).select_related("knowledge")
        for account in accounts:
            try:
                # ReplyLog's (account, message_id) uniqueness makes re-seen replies
                # no-ops, so no polling cursor is needed.
                for event in threads.fetch_new_replies(account):
                    handle_inbound(account, **event)
            except Exception:
                logger.exception("threads poll failed for account %s", account.id)
