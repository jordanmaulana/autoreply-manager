"""WhatsApp Cloud API (graph.facebook.com). Accounts are connected by pasting
WABA credentials (phone_number_id + permanent system-user token) — Embedded
Signup requires business verification and is out of MVP scope."""

import logging

import httpx

from core.models import SocialAccount
from core.social.meta_common import GRAPH_VERSION, raise_for_graph_error

logger = logging.getLogger(__name__)

TIMEOUT = 15


def fetch_phone_profile(phone_number_id: str, access_token: str) -> dict:
    """Validate pasted credentials by reading the phone number profile."""
    resp = httpx.get(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_number_id}",
        params={"fields": "display_phone_number,verified_name"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    return resp.json()


def send_reply(account: SocialAccount, recipient_id: str, text: str, _inbound_id: str) -> str:
    resp = httpx.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{account.platform_user_id}/messages",
        headers={"Authorization": f"Bearer {account.access_token}"},
        json={
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text},
        },
        timeout=TIMEOUT,
    )
    raise_for_graph_error(resp)
    messages = resp.json().get("messages") or [{}]
    return messages[0].get("id", "")


def parse_webhook_events(payload: dict) -> list[dict]:
    """Flatten a webhook payload into inbound text-message events.

    Ignores `statuses[]` (delivery receipts — WhatsApp's echo source) and any
    non-text message types."""
    events = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            phone_number_id = str((value.get("metadata") or {}).get("phone_number_id", ""))
            contacts = {
                c.get("wa_id"): (c.get("profile") or {}).get("name", "")
                for c in value.get("contacts", [])
            }
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                sender = str(message.get("from", ""))
                events.append(
                    {
                        "account_platform_user_id": phone_number_id,
                        "platform_message_id": message.get("id", ""),
                        "sender_id": sender,
                        "sender_name": contacts.get(sender, ""),
                        "text": (message.get("text") or {}).get("body", ""),
                    }
                )
    return events
