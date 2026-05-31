"""Knowledge base admin."""
from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "format", "chunk_count", "file_size", "created_at"]
    search_fields = ["name"]
    list_filter = ["format"]
