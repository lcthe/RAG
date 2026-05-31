"""Chat models."""
import uuid
from django.db import models

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, verbose_name="标题")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "对话"
        verbose_name_plural = "对话"

    def __str__(self):
        return self.title or f"对话 #{self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages", verbose_name="对话")
    role = models.CharField(max_length=20, verbose_name="角色")
    content = models.TextField(verbose_name="内容")
    sources = models.JSONField(default=list, blank=True, verbose_name="来源")
    latency_ms = models.FloatField(default=0, verbose_name="耗时(ms)")
    model_used = models.CharField(max_length=100, blank=True, verbose_name="模型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["created_at"]
        verbose_name = "消息"
        verbose_name_plural = "消息"

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"

class QueryLog(models.Model):
    question = models.TextField(verbose_name="问题")
    answer_preview = models.CharField(max_length=200, blank=True, verbose_name="回答预览")
    latency_ms = models.FloatField(default=0, verbose_name="耗时(ms)")
    retrieval_count = models.IntegerField(default=0, verbose_name="检索条数")
    model_used = models.CharField(max_length=100, blank=True, verbose_name="模型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "查询日志"
        verbose_name_plural = "查询日志"
