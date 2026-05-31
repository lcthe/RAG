from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer
from apps.chat.models import QueryLog
from services.rag_service import rag_service

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    
    @action(detail=False, methods=["post"])
    def upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        import os, uuid
        from django.conf import settings
        upload_dir = os.path.join(settings.DATA_DIR, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{file.name}")
        with open(path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        doc = Document.objects.create(name=file.name, file_path=path, file_size=file.size, format=os.path.splitext(file.name)[1].lstrip("."))
        chunks = rag_service.ingest_file(path)
        doc.chunk_count = chunks
        doc.save()
        return Response({"status": "ok", "filename": file.name, "chunks": chunks})
    
    @action(detail=False, methods=["post"])
    def reload(self, request):
        rag_service.reload()
        return Response({"status": "ok", "message": "Reload started"})
