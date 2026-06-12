import logging

from django.db import IntegrityError, close_old_connections

from core.models import ReplyLog, SocialAccount
from core.rag.answer import SkipReply, generate_reply

logger = logging.getLogger(__name__)


def handle_inbound(
    account: SocialAccount,
    platform_message_id: str,
    sender_id: str,
    text: str,
    sender_name: str = "",
):
    """Process one inbound message end-to-end. Safe to call repeatedly with the
    same message id: the (account, platform_message_id) unique constraint makes
    duplicates no-ops, which covers webhook retries and multi-worker races."""
    if sender_id == account.platform_user_id:
        return

    try:
        log = ReplyLog.objects.create(
            account=account,
            actor=account.actor,
            platform_message_id=platform_message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            inbound_text=text,
        )
    except IntegrityError:
        return  # already handled

    if not account.auto_reply_enabled:
        log.status = ReplyLog.Status.SKIPPED
        log.error = "Auto-reply is disabled for this account."
        log.save(update_fields=["status", "error", "updated_on"])
        return

    log.status = ReplyLog.Status.PROCESSING
    log.save(update_fields=["status", "updated_on"])
    try:
        reply, retrieved = generate_reply(account, text)
        log.reply_text = reply
        log.retrieved_chunks = retrieved
        from core.social import get_sender

        sent_id = get_sender(account.platform)(account, sender_id, reply, platform_message_id)
        log.sent_message_id = sent_id or ""
        log.status = ReplyLog.Status.SENT
    except SkipReply as exc:
        log.status = ReplyLog.Status.SKIPPED
        log.error = str(exc)
    except Exception as exc:
        logger.exception("auto-reply failed for account %s msg %s", account.id, platform_message_id)
        log.status = ReplyLog.Status.FAILED
        log.error = str(exc)[:2000]
    log.save()


def handle_inbound_threadsafe(account_id: str, **kwargs):
    """Entry point for daemon threads spawned by webhook views."""
    close_old_connections()
    try:
        account = SocialAccount.objects.select_related("knowledge").get(id=account_id)
        handle_inbound(account, **kwargs)
    finally:
        close_old_connections()
