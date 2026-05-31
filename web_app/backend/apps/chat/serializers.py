from rest_framework import serializers
from .models import Conversation, Message, QueryLog

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "sources", "latency_ms", "model_used", "created_at"]

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ["id", "title", "messages", "created_at", "updated_at"]

class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ["id", "title", "message_count", "created_at"]
    
    def get_message_count(self, obj):
        return obj.messages.count()

class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = ["id", "question", "answer_preview", "latency_ms", "retrieval_count", "model_used", "created_at"]

class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, default=None)
