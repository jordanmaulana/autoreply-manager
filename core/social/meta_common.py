import hashlib
import hmac
import logging

from django.conf import settings
from django.core import signing

logger = logging.getLogger(__name__)

GRAPH_VERSION = "v23.0"
STATE_MAX_AGE_SECONDS = 600


class SocialApiError(Exception):
    pass


def verify_hub_challenge(request) -> str | None:
    """Meta webhook GET handshake. Returns the challenge to echo, or None."""
    if request.query_params.get("hub.mode") != "subscribe":
        return None
    if request.query_params.get("hub.verify_token") != settings.META_WEBHOOK_VERIFY_TOKEN:
        return None
    return request.query_params.get("hub.challenge")


def verify_signature(request, app_secret: str) -> bool:
    """Validate X-Hub-Signature-256 over the raw request body."""
    if not app_secret:
        logger.error("webhook signature check skipped: app secret not configured")
        return False
    received = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(app_secret.encode(), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def sign_state(user_id: int) -> str:
    return signing.TimestampSigner(salt="social-oauth").sign(str(user_id))


def unsign_state(state: str) -> int:
    """Returns the user id; raises signing.BadSignature on tampering/expiry."""
    value = signing.TimestampSigner(salt="social-oauth").unsign(
        state, max_age=STATE_MAX_AGE_SECONDS
    )
    return int(value)


def raise_for_graph_error(resp):
    if resp.status_code >= 400:
        raise SocialApiError(f"Graph API {resp.status_code}: {resp.text[:500]}")
