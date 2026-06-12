from django.urls import path

from api.v1 import (
    accounts_api,
    auth_api,
    knowledge_api,
    payments_api,
    replies_api,
    webhooks_api,
)

urlpatterns = [
    path("auth/google/", auth_api.google, name="api-v1-auth-google"),
    path("auth/register/", auth_api.register, name="api-v1-auth-register"),
    path("auth/login/", auth_api.login, name="api-v1-auth-login"),
    path("auth/logout/", auth_api.logout, name="api-v1-logout"),
    path("auth/me/", auth_api.me, name="api-v1-me"),
    path("payments/mayar/webhook/", payments_api.webhook, name="api-v1-mayar-webhook"),
    path("knowledge/", knowledge_api.knowledge_list, name="api-v1-knowledge"),
    path("knowledge/<str:knowledge_id>/", knowledge_api.knowledge_detail),
    path("knowledge/<str:knowledge_id>/rebuild/", knowledge_api.knowledge_rebuild),
    path("knowledge/<str:knowledge_id>/query/", knowledge_api.knowledge_query),
    path("accounts/", accounts_api.account_list, name="api-v1-accounts"),
    path("accounts/whatsapp/", accounts_api.whatsapp_connect),
    path("accounts/<str:platform>/connect/", accounts_api.connect),
    path("accounts/<str:platform>/callback/", accounts_api.callback),
    path("accounts/<str:account_id>/", accounts_api.account_detail),
    path("replies/", replies_api.reply_list, name="api-v1-replies"),
    path("webhooks/instagram/", webhooks_api.instagram_webhook),
    path("webhooks/whatsapp/", webhooks_api.whatsapp_webhook),
]
