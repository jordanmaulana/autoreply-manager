from django.contrib import admin

from core.models import AppSetting, Knowledge, KnowledgeChunk, ReplyLog, SocialAccount


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ["key", "str_value", "int_value", "float_value", "bool_value"]
    search_fields = ["key"]


@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ["title", "actor", "status", "chunk_count", "embedded_on", "created_on"]
    list_filter = ["status"]
    search_fields = ["title"]


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ["knowledge", "seq", "token_count", "created_on"]
    raw_id_fields = ["knowledge"]


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = [
        "platform",
        "username",
        "platform_user_id",
        "actor",
        "status",
        "auto_reply_enabled",
        "knowledge",
        "token_expires_on",
    ]
    list_filter = ["platform", "status"]
    search_fields = ["username", "platform_user_id"]


@admin.register(ReplyLog)
class ReplyLogAdmin(admin.ModelAdmin):
    list_display = ["account", "sender_id", "status", "created_on"]
    list_filter = ["status", "account__platform"]
    search_fields = ["sender_id", "inbound_text"]
    raw_id_fields = ["account"]
