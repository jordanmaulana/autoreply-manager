import logging
import threading

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import SocialAccount
from core.rag.inbound import handle_inbound_threadsafe
from core.social import instagram, whatsapp
from core.social.meta_common import verify_hub_challenge, verify_signature

logger = logging.getLogger(__name__)


def _process_events(platform: str, events: list[dict]):
    """Resolve accounts and run the auto-reply pipeline. Runs inside a daemon thread."""
    for event in events:
        account = (
            SocialAccount.objects.filter(
                platform=platform,
                platform_user_id=event.pop("account_platform_user_id"),
                status=SocialAccount.Status.CONNECTED,
            )
            .only("id")
            .first()
        )
        if not account:
            logger.warning("%s webhook: no connected account for event, skipping", platform)
            continue
        handle_inbound_threadsafe(account.id, **event)


def _webhook(request, platform: str, app_secret: str, parse):
    if request.method == "GET":
        challenge = verify_hub_challenge(request)
        if challenge is None:
            return Response({"detail": "verification failed"}, status=403)
        return HttpResponse(challenge, content_type="text/plain")

    if not verify_signature(request, app_secret):
        return Response({"detail": "invalid signature"}, status=401)

    events = parse(request.data)
    if events:
        threading.Thread(target=_process_events, args=(platform, events), daemon=True).start()
    return Response({"ok": True})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def instagram_webhook(request):
    return _webhook(
        request,
        SocialAccount.Platform.INSTAGRAM,
        settings.INSTAGRAM_APP_SECRET,
        instagram.parse_webhook_events,
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    return _webhook(
        request,
        SocialAccount.Platform.WHATSAPP,
        settings.WHATSAPP_APP_SECRET,
        whatsapp.parse_webhook_events,
    )
