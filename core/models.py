from bson.objectid import ObjectId
from django.contrib.auth.models import User
from django.db import models
from pgvector.django import VectorField

EMBEDDING_DIMENSIONS = 1536


def make_object_id():
    return str(ObjectId())


class BaseModel(models.Model):
    id = models.CharField(primary_key=True, default=make_object_id, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True
        ordering = ["id"]
        indexes = [models.Index(fields=["created_on"])]

    def __str__(self):
        return f"{self.id}"


class AppSetting(models.Model):
    key = models.CharField()
    should_be_unique = models.BooleanField(default=True)
    str_value = models.TextField(null=True, blank=True)
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    bool_value = models.BooleanField(default=True)

    class Meta:
        app_label = "core"

    @staticmethod
    def get(key, value_type, default=None):
        if value_type not in ["str", "int", "float", "bool"]:
            raise ValueError("Value type should be one of str, int, float, or bool")
        try:
            setting = AppSetting.objects.get(key__iexact=key)
            return getattr(setting, f"{value_type}_value")
        except AppSetting.DoesNotExist:
            return default

    def __str__(self):
        return self.key


class Knowledge(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        READY = "ready"
        FAILED = "failed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    persona = models.TextField(blank=True, default="")
    status = models.CharField(choices=Status.choices, default=Status.PENDING)
    status_error = models.TextField(blank=True, default="")
    chunk_count = models.PositiveIntegerField(default=0)
    embedding_model = models.CharField(default="text-embedding-3-small")
    description_sha256 = models.CharField(max_length=64, blank=True, default="")
    embedded_on = models.DateTimeField(null=True, blank=True)
    embedding_started_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class KnowledgeChunk(BaseModel):
    knowledge = models.ForeignKey(Knowledge, related_name="chunks", on_delete=models.CASCADE)
    seq = models.PositiveIntegerField()
    text = models.TextField()
    token_count = models.PositiveIntegerField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)

    class Meta(BaseModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["knowledge", "seq"], name="uniq_kchunk_knowledge_seq"),
        ]


class SocialAccount(BaseModel):
    class Platform(models.TextChoices):
        INSTAGRAM = "instagram"
        WHATSAPP = "whatsapp"
        THREADS = "threads"

    class Status(models.TextChoices):
        CONNECTED = "connected"
        EXPIRED = "expired"
        DISCONNECTED = "disconnected"

    platform = models.CharField(choices=Platform.choices)
    # IG-scoped user id / WhatsApp phone_number_id / Threads user id
    platform_user_id = models.CharField()
    username = models.CharField(blank=True, default="")
    access_token = models.TextField(blank=True, default="")
    token_expires_on = models.DateTimeField(null=True, blank=True)
    knowledge = models.ForeignKey(
        Knowledge, null=True, blank=True, on_delete=models.SET_NULL, related_name="accounts"
    )
    status = models.CharField(choices=Status.choices, default=Status.CONNECTED)
    auto_reply_enabled = models.BooleanField(default=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "platform_user_id"], name="uniq_account_platform_uid"
            ),
        ]

    def __str__(self):
        return f"{self.platform}:{self.username or self.platform_user_id}"


class ReplyLog(BaseModel):
    class Status(models.TextChoices):
        RECEIVED = "received"
        PROCESSING = "processing"
        SENT = "sent"
        FAILED = "failed"
        SKIPPED = "skipped"

    account = models.ForeignKey(SocialAccount, related_name="replies", on_delete=models.CASCADE)
    platform_message_id = models.CharField()
    sender_id = models.CharField()
    sender_name = models.CharField(blank=True, default="")
    inbound_text = models.TextField()
    reply_text = models.TextField(blank=True, default="")
    retrieved_chunks = models.JSONField(default=list, blank=True)
    status = models.CharField(choices=Status.choices, default=Status.RECEIVED)
    error = models.TextField(blank=True, default="")
    sent_message_id = models.CharField(blank=True, default="")

    class Meta(BaseModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(
                fields=["account", "platform_message_id"], name="uniq_replylog_account_msg"
            ),
        ]
