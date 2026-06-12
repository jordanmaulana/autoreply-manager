"""Threads API (graph.threads.net). No DM API exists; auto-reply targets
replies to the user's own posts, discovered by polling (reply webhooks need
Advanced Access + app review, out of MVP scope)."""

import logging
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.utils import timezone

from core.models import SocialAccount
from core.social.meta_common import raise_for_graph_error

logger = logging.getLogger(__name__)

SCOPES = "threads_basic,threads_read_replies,threads_manage_replies,threads_content_publish"
TIMEOUT = 15
BASE = "https://graph.threads.net/v1.0"
RECENT_POSTS_LIMIT = 10
RECENT_POSTS_DAYS = 7


def redirect_uri() -> str:
    return f"{settings.SITE_URL}/api/v1/accounts/threads/callback/"


def authorize_url(state: str) -> str:
    params = {
        "client_id": settings.THREADS_APP_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    return f"https://threads.net/oauth/authorize?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    resp = httpx.post(
        "https://graph.threads.net/oauth/access_token",
        data={
            "client_id": settings.THREADS_APP_ID,
            "client_secret": settings.THREADS_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri(),
            "code": code,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    short_token = resp.json()["access_token"]

    resp = httpx.get(
        "https://graph.threads.net/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": settings.THREADS_APP_SECRET,
            "access_token": short_token,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    data = resp.json()
    token = data["access_token"]
    expires_on = timezone.now() + timedelta(seconds=data.get("expires_in", 5184000))

    resp = httpx.get(
        f"{BASE}/me",
        params={"fields": "id,username", "access_token": token},
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    me = resp.json()
    return {
        "access_token": token,
        "token_expires_on": expires_on,
        "platform_user_id": str(me["id"]),
        "username": me.get("username", ""),
    }


def refresh_token(account: SocialAccount) -> bool:
    try:
        resp = httpx.get(
            "https://graph.threads.net/refresh_access_token",
            params={"grant_type": "th_refresh_token", "access_token": account.access_token},
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
        logger.exception("threads token refresh failed for %s", account.id)
        account.status = SocialAccount.Status.EXPIRED
        account.save(update_fields=["status", "updated_on"])
        return False


def fetch_new_replies(account: SocialAccount) -> list[dict]:
    """Poll recent own posts and collect replies from other users."""
    since = int((timezone.now() - timedelta(days=RECENT_POSTS_DAYS)).timestamp())
    resp = httpx.get(
        f"{BASE}/me/threads",
        params={
            "fields": "id",
            "limit": RECENT_POSTS_LIMIT,
            "since": since,
            "access_token": account.access_token,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    events = []
    for post in resp.json().get("data", []):
        resp = httpx.get(
            f"{BASE}/{post['id']}/replies",
            params={
                "fields": "id,text,username",
                "access_token": account.access_token,
            },
            timeout=TIMEOUT,
        )
        raise_for_graph_error(resp)
        for reply in resp.json().get("data", []):
            if not reply.get("text") or reply.get("username") == account.username:
                continue
            events.append(
                {
                    "platform_message_id": str(reply["id"]),
                    "sender_id": reply.get("username", ""),
                    "sender_name": reply.get("username", ""),
                    "text": reply["text"],
                }
            )
    return events


def send_reply(account: SocialAccount, _recipient_id: str, text: str, inbound_id: str) -> str:
    """Publish a reply to the inbound Threads reply (two-step create + publish)."""
    resp = httpx.post(
        f"{BASE}/me/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": inbound_id,
            "access_token": account.access_token,
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    creation_id = resp.json()["id"]
    resp = httpx.post(
        f"{BASE}/me/threads_publish",
        params={"creation_id": creation_id, "access_token": account.access_token},
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    return str(resp.json().get("id", ""))
