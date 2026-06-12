"""Instagram API with Instagram Login (graph.instagram.com)."""

import logging
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.utils import timezone

from core.models import SocialAccount
from core.social.meta_common import GRAPH_VERSION, raise_for_graph_error

logger = logging.getLogger(__name__)

SCOPES = "instagram_business_basic,instagram_business_manage_messages"
TIMEOUT = 15


def redirect_uri() -> str:
    return f"{settings.SITE_URL}/api/v1/accounts/instagram/callback/"


def authorize_url(state: str) -> str:
    params = {
        "client_id": settings.INSTAGRAM_APP_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    return f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """code -> short-lived token -> long-lived token (~60 days) + profile."""
    resp = httpx.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": settings.INSTAGRAM_APP_ID,
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri(),
            "code": code,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    short_token = resp.json()["access_token"]

    resp = httpx.get(
        "https://graph.instagram.com/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "access_token": short_token,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    data = resp.json()
    token = data["access_token"]
    expires_on = timezone.now() + timedelta(seconds=data.get("expires_in", 5184000))

    resp = httpx.get(
        f"https://graph.instagram.com/{GRAPH_VERSION}/me",
        params={"fields": "user_id,username", "access_token": token},
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    me = resp.json()
    return {
        "access_token": token,
        "token_expires_on": expires_on,
        "platform_user_id": str(me.get("user_id") or me.get("id")),
        "username": me.get("username", ""),
    }


def refresh_token(account: SocialAccount) -> bool:
    """Refresh a long-lived token in place. Returns False (and marks EXPIRED) on failure."""
    try:
        resp = httpx.get(
            "https://graph.instagram.com/refresh_access_token",
            params={"grant_type": "ig_refresh_token", "access_token": account.access_token},
            timeout=TIMEOUT,
        )
        raise_for_graph_error(resp)
        data = resp.json()
        account.access_token = data["access_token"]
        account.token_expires_on = timezone.now() + timedelta(
            seconds=data.get("expires_in", 5184000)
        )
        account.status = SocialAccount.Status.CONNECTED
        account.save(update_fields=["access_token", "token_expires_on", "status", "updated_on"])
        return True
    except Exception:
        logger.exception("instagram token refresh failed for %s", account.id)
        account.status = SocialAccount.Status.EXPIRED
        account.save(update_fields=["status", "updated_on"])
        return False


def send_reply(account: SocialAccount, recipient_id: str, text: str, _inbound_id: str) -> str:
    resp = httpx.post(
        f"https://graph.instagram.com/{GRAPH_VERSION}/me/messages",
        headers={"Authorization": f"Bearer {account.access_token}"},
        json={"recipient": {"id": recipient_id}, "message": {"text": text}},
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    return resp.json().get("message_id", "")


def parse_webhook_events(payload: dict) -> list[dict]:
    """Flatten a webhook payload into inbound text-DM events."""
    events = []
    for entry in payload.get("entry", []):
        ig_user_id = str(entry.get("id", ""))
        for item in entry.get("messaging", []):
            message = item.get("message") or {}
            text = message.get("text", "")
            if message.get("is_echo") or not text:
                continue
            sender_id = str((item.get("sender") or {}).get("id", ""))
            if not sender_id or sender_id == ig_user_id:
                continue
            events.append(
                {
                    "account_platform_user_id": ig_user_id,
                    "platform_message_id": message.get("mid", ""),
                    "sender_id": sender_id,
                    "text": text,
                }
            )
    return events
