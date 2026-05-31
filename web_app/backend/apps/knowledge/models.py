"""Knowledge base models."""
from django.db import models

class Document(models.Model):
    name = models.CharField(max_length=255, verbose_name="文档名")
    file_path = models.TextField(blank=True, verbose_name="文件路径")
    file_size = models.IntegerField(default=0, verbose_name="文件大小")
    format = models.CharField(max_length=20, blank=True, verbose_name="格式")
    chunk_count = models.IntegerField(default=0, verbose_name="分块数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "文档"
        verbose_name_plural = "文档"

    def __str__(self):
        return self.name
