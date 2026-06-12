def get_sender(platform: str):
    """Return send_reply(account, recipient_id, text, inbound_message_id) for a platform."""
    from core.models import SocialAccount
    from core.social import instagram, threads, whatsapp

    return {
        SocialAccount.Platform.INSTAGRAM: instagram.send_reply,
        SocialAccount.Platform.WHATSAPP: whatsapp.send_reply,
        SocialAccount.Platform.THREADS: threads.send_reply,
    }[platform]
