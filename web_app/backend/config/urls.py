from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok", "service": "rag-api"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.chat.urls")),
    path("api/admin/", include("apps.knowledge.urls")),
    path("api/health/", health),
]
