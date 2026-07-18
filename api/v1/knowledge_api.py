from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.v1.serializers import KnowledgeSerializer
from core.models import Knowledge
from core.rag.runner import description_hash, start_embedding_job

MAX_DESCRIPTION_CHARS = 2_000_000  # ~a long book; guards accidental megapastes


def _get_owned(request, knowledge_id) -> Knowledge:
    return get_object_or_404(Knowledge, id=knowledge_id, actor=request.user)


def _validate_description_size(description: str):
    if len(description) > MAX_DESCRIPTION_CHARS:
        return Response(
            {"detail": f"Description exceeds {MAX_DESCRIPTION_CHARS} characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


@api_view(["GET", "POST"])
def knowledge_list(request):
    if request.method == "GET":
        qs = Knowledge.objects.filter(actor=request.user).order_by("-created_on")
        return Response(KnowledgeSerializer(qs, many=True).data)

    if Knowledge.objects.filter(actor=request.user).count() >= settings.MAX_KNOWLEDGE_PER_USER:
        return Response(
            {"detail": f"Knowledge base limit reached ({settings.MAX_KNOWLEDGE_PER_USER})."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = KnowledgeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if error := _validate_description_size(serializer.validated_data["description"]):
        return error
    knowledge = serializer.save(actor=request.user)
    start_embedding_job(knowledge.id)
    knowledge.refresh_from_db()
    return Response(KnowledgeSerializer(knowledge).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def knowledge_detail(request, knowledge_id):
    knowledge = _get_owned(request, knowledge_id)

    if request.method == "GET":
        return Response(KnowledgeSerializer(knowledge).data)

    if request.method == "DELETE":
        knowledge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = KnowledgeSerializer(knowledge, data=request.data)
    serializer.is_valid(raise_exception=True)
    if error := _validate_description_size(serializer.validated_data["description"]):
        return error
    description_changed = (
        description_hash(serializer.validated_data["description"]) != knowledge.description_sha256
    )
    knowledge = serializer.save()
    if description_changed:
        Knowledge.objects.filter(id=knowledge.id).update(status=Knowledge.Status.PENDING)
        start_embedding_job(knowledge.id)
        knowledge.refresh_from_db()
    return Response(KnowledgeSerializer(knowledge).data)


@api_view(["POST"])
def knowledge_query(request, knowledge_id):
    """Debug endpoint: run the full RAG flow without sending anything."""
    knowledge = _get_owned(request, knowledge_id)
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response({"detail": "question is required"}, status=status.HTTP_400_BAD_REQUEST)
    if knowledge.status != Knowledge.Status.READY:
        return Response(
            {"detail": f"Knowledge is not ready (status: {knowledge.status})."},
            status=status.HTTP_409_CONFLICT,
        )

    from core.models import SocialAccount
    from core.rag.answer import generate_reply

    probe = SocialAccount(
        platform=SocialAccount.Platform.WHATSAPP,
        platform_user_id="debug",
        username="debug",
        knowledge=knowledge,
    )
    reply, retrieved = generate_reply(probe, question)
    return Response({"reply": reply, "retrieved_chunks": retrieved})


@api_view(["POST"])
def knowledge_rebuild(request, knowledge_id):
    knowledge = _get_owned(request, knowledge_id)
    if not start_embedding_job(knowledge.id):
        return Response(
            {"detail": "Embedding already in progress."}, status=status.HTTP_409_CONFLICT
        )
    knowledge.refresh_from_db()
    return Response(KnowledgeSerializer(knowledge).data)
