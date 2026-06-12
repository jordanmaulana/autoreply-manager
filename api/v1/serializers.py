from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers

from core.models import Knowledge, ReplyLog, SocialAccount


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)


class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.CharField()

    def validate(self, attrs):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise serializers.ValidationError("Google OAuth not configured")
        try:
            claims = id_token.verify_oauth2_token(
                attrs["credential"],
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except ValueError as exc:
            raise serializers.ValidationError(f"Invalid Google credential: {exc}") from exc
        if not claims.get("email_verified"):
            raise serializers.ValidationError("Email not verified")
        attrs["claims"] = claims
        return attrs


class EmailRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate_email(self, value):
        return value.lower()


class KnowledgeSerializer(serializers.ModelSerializer):
    account_count = serializers.IntegerField(source="accounts.count", read_only=True)

    class Meta:
        model = Knowledge
        fields = [
            "id",
            "title",
            "description",
            "persona",
            "status",
            "status_error",
            "chunk_count",
            "embedded_on",
            "account_count",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "id",
            "status",
            "status_error",
            "chunk_count",
            "embedded_on",
            "account_count",
            "created_on",
            "updated_on",
        ]


class SocialAccountSerializer(serializers.ModelSerializer):
    knowledge_id = serializers.PrimaryKeyRelatedField(
        source="knowledge", queryset=Knowledge.objects.none(), allow_null=True, required=False
    )
    knowledge_title = serializers.CharField(source="knowledge.title", read_only=True, default="")

    class Meta:
        model = SocialAccount
        # access_token is intentionally never exposed
        fields = [
            "id",
            "platform",
            "platform_user_id",
            "username",
            "status",
            "auto_reply_enabled",
            "knowledge_id",
            "knowledge_title",
            "token_expires_on",
            "created_on",
        ]
        read_only_fields = [
            "id",
            "platform",
            "platform_user_id",
            "username",
            "status",
            "token_expires_on",
            "created_on",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["knowledge_id"].queryset = Knowledge.objects.filter(actor=request.user)


class WhatsAppConnectSerializer(serializers.Serializer):
    phone_number_id = serializers.CharField()
    access_token = serializers.CharField()


class ReplyLogSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="account.platform", read_only=True)
    account_username = serializers.CharField(source="account.username", read_only=True)

    class Meta:
        model = ReplyLog
        fields = [
            "id",
            "account_id",
            "platform",
            "account_username",
            "platform_message_id",
            "sender_id",
            "sender_name",
            "inbound_text",
            "reply_text",
            "retrieved_chunks",
            "status",
            "error",
            "created_on",
        ]
