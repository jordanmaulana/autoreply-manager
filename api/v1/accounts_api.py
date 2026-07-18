import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.v1.serializers import SocialAccountSerializer, WhatsAppConnectSerializer
from core.models import SocialAccount, User
from core.social import instagram, threads, whatsapp
from core.social.meta_common import SocialApiError, sign_state, unsign_state

logger = logging.getLogger(__name__)

OAUTH_PLATFORMS = {
    SocialAccount.Platform.INSTAGRAM: instagram,
    SocialAccount.Platform.THREADS: threads,
}


def _account_limit_reached(user, platform, platform_user_id) -> bool:
    """True only when adding a genuinely new account would exceed the per-user cap.
    Reconnecting an already-owned account (update path) is always allowed."""
    if SocialAccount.objects.filter(
        platform=platform, platform_user_id=platform_user_id, actor=user
    ).exists():
        return False
    return SocialAccount.objects.filter(actor=user).count() >= settings.MAX_ACCOUNTS_PER_USER


@api_view(["GET"])
def account_list(request):
    qs = (
        SocialAccount.objects.filter(actor=request.user)
        .select_related("knowledge")
        .order_by("platform", "username")
    )
    return Response(SocialAccountSerializer(qs, many=True).data)


@api_view(["GET"])
def connect(request, platform):
    module = OAUTH_PLATFORMS.get(platform)
    if not module:
        return Response(
            {"detail": f"OAuth connect not supported for {platform}."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response({"url": module.authorize_url(sign_state(request.user.id))})


@api_view(["GET"])
@permission_classes([AllowAny])
def callback(request, platform):
    """OAuth redirect target — browser request, no auth header; user comes from signed state."""
    from django.conf import settings

    def bounce(**params):
        return redirect(f"{settings.FRONTEND_URL}/accounts?{urlencode(params)}")

    module = OAUTH_PLATFORMS.get(platform)
    if not module:
        return bounce(error=f"unknown platform {platform}")
    if request.query_params.get("error"):
        return bounce(error=request.query_params.get("error_description") or "access denied")

    try:
        user_id = unsign_state(request.query_params.get("state", ""))
        user = User.objects.get(id=user_id)
        data = module.exchange_code(request.query_params.get("code", ""))
    except signing.BadSignature:
        return bounce(error="Connection link expired, please try again.")
    except (SocialApiError, KeyError, User.DoesNotExist) as exc:
        logger.exception("%s oauth callback failed", platform)
        return bounce(error=str(exc)[:200])

    if _account_limit_reached(user, platform, data["platform_user_id"]):
        return bounce(error=f"Account limit reached ({settings.MAX_ACCOUNTS_PER_USER}).")

    SocialAccount.objects.update_or_create(
        platform=platform,
        platform_user_id=data["platform_user_id"],
        defaults={
            "actor": user,
            "username": data["username"],
            "access_token": data["access_token"],
            "token_expires_on": data["token_expires_on"],
            "status": SocialAccount.Status.CONNECTED,
        },
    )
    return bounce(connected=platform)


@api_view(["POST"])
def whatsapp_connect(request):
    serializer = WhatsAppConnectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone_number_id = serializer.validated_data["phone_number_id"]
    access_token = serializer.validated_data["access_token"]

    if _account_limit_reached(request.user, SocialAccount.Platform.WHATSAPP, phone_number_id):
        return Response(
            {"detail": f"Account limit reached ({settings.MAX_ACCOUNTS_PER_USER})."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        profile = whatsapp.fetch_phone_profile(phone_number_id, access_token)
    except SocialApiError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    account, _ = SocialAccount.objects.update_or_create(
        platform=SocialAccount.Platform.WHATSAPP,
        platform_user_id=phone_number_id,
        defaults={
            "actor": request.user,
            "username": profile.get("display_phone_number", ""),
            "access_token": access_token,
            "token_expires_on": None,
            "status": SocialAccount.Status.CONNECTED,
            "extra": {"verified_name": profile.get("verified_name", "")},
        },
    )
    return Response(
        SocialAccountSerializer(account, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
def account_detail(request, account_id):
    account = get_object_or_404(SocialAccount, id=account_id, actor=request.user)

    if request.method == "DELETE":
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SocialAccountSerializer(
        account, data=request.data, partial=True, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
