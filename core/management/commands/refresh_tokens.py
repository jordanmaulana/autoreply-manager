from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import SocialAccount
from core.social import instagram, threads

REFRESH_WINDOW_DAYS = 10


class Command(BaseCommand):
    help = "Refresh Instagram/Threads long-lived tokens that expire soon. Run daily via cron."

    def handle(self, *args, **options):
        cutoff = timezone.now() + timedelta(days=REFRESH_WINDOW_DAYS)
        accounts = SocialAccount.objects.filter(
            platform__in=[SocialAccount.Platform.INSTAGRAM, SocialAccount.Platform.THREADS],
            status=SocialAccount.Status.CONNECTED,
            token_expires_on__lt=cutoff,
        )
        refreshed = failed = 0
        for account in accounts:
            module = instagram if account.platform == SocialAccount.Platform.INSTAGRAM else threads
            if module.refresh_token(account):
                refreshed += 1
            else:
                failed += 1
        self.stdout.write(f"refreshed={refreshed} failed={failed}")
