"""Chat admin."""
from django.contrib import admin
from .models import Conversation, Message, QueryLog

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "created_at", "updated_at"]
    search_fields = ["title"]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "content_preview", "latency_ms", "created_at"]
    list_filter = ["role"]
    
    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = "内容预览"

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ["question", "answer_preview", "latency_ms", "model_used", "created_at"]
    list_filter = ["model_used"]
