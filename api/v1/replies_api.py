from rest_framework.decorators import api_view
from rest_framework.pagination import LimitOffsetPagination

from api.v1.serializers import ReplyLogSerializer
from core.models import ReplyLog


@api_view(["GET"])
def reply_list(request):
    qs = (
        ReplyLog.objects.filter(account__actor=request.user)
        .select_related("account")
        .order_by("-created_on")
    )
    if account_id := request.query_params.get("account"):
        qs = qs.filter(account_id=account_id)
    if status_filter := request.query_params.get("status"):
        qs = qs.filter(status=status_filter)

    paginator = LimitOffsetPagination()
    paginator.default_limit = 50
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(ReplyLogSerializer(page, many=True).data)
