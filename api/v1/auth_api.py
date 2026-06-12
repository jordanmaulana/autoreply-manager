from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.v1.serializers import (
    EmailLoginSerializer,
    EmailRegisterSerializer,
    GoogleAuthSerializer,
    UserSerializer,
)

User = get_user_model()


def _auth_response(user, created=False):
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def google(request):
    serializer = GoogleAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    claims = serializer.validated_data["claims"]
    email = claims["email"].lower()
    with transaction.atomic():
        user, created = User.objects.get_or_create(
            email__iexact=email,
            defaults={"username": email, "email": email},
        )
    return _auth_response(user, created=created)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = EmailRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    with transaction.atomic():
        # Reject existing emails instead of setting a password: without email
        # verification, the latter would let anyone hijack a Google-created account.
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"detail": "Email already registered — sign in instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(
            username=email, email=email, password=serializer.validated_data["password"]
        )
    return _auth_response(user, created=True)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = EmailLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
    if not user or not user.check_password(serializer.validated_data["password"]):
        # Same message for unknown email, wrong password, and password-less
        # Google accounts — avoids user enumeration.
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return _auth_response(user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
