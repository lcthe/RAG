"""Chat API views."""
import json, time, uuid
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import Conversation, Message, QueryLog
from .serializers import (
    ConversationSerializer, ConversationListSerializer,
    MessageSerializer, QueryLogSerializer, ChatRequestSerializer,
)
from services.rag_service import rag_service

@api_view(["POST"])
def chat(request):
    ser = ChatRequestSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    question = ser.validated_data["question"]
    top_k = ser.validated_data.get("top_k")
    
    try:
        result = rag_service.query(question, top_k)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    QueryLog.objects.create(
        question=question,
        answer_preview=result.get("answer", "")[:200],
        latency_ms=result.get("latency_ms", 0),
        retrieval_count=result.get("retrieval_count", 0),
        model_used=result.get("model", ""),
    )
    
    return Response(result)

@api_view(["GET"])
def info(request):
    try:
        return Response(rag_service.get_info())
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ====== 对话历史管理 ======

@api_view(["GET"])
def list_conversations(request):
    convs = Conversation.objects.all().order_by("-created_at")
    ser = ConversationListSerializer(convs, many=True)
    return Response(ser.data)

@api_view(["GET"])
def get_conversation_detail(request, conv_id):
    try:
        conv = Conversation.objects.get(id=conv_id)
    except Conversation.DoesNotExist:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    ser = ConversationSerializer(conv)
    return Response(ser.data)

@api_view(["POST"])
def save_conversation(request):
    data = request.data
    conv_id = data.get("id")
    messages = data.get("messages", [])
    title = data.get("title", "")

    with transaction.atomic():
        if conv_id:
            try:
                conv = Conversation.objects.get(id=conv_id)
            except Conversation.DoesNotExist:
                conv = Conversation(id=conv_id)
        else:
            conv = Conversation()
        if title:
            conv.title = title
        conv.save()
        conv.messages.all().delete()
        for msg in messages:
            Message.objects.create(
                conversation=conv,
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                sources=msg.get("sources", []),
                latency_ms=msg.get("latency_ms", 0),
                model_used=msg.get("model", ""),
            )
    return Response({"status": "ok", "id": str(conv.id)})

@api_view(["DELETE"])
def delete_conversation(request, conv_id):
    Conversation.objects.filter(id=conv_id).delete()
    return Response({"status": "ok"})

