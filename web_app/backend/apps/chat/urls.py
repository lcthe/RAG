from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat, name="chat"),
    path("chat/info/", views.info, name="chat-info"),
    path("chat/history/", views.ConversationViewSet.as_view({"get": "list"}), name="history-list"),
    path("chat/history/save/", views.save_conversation, name="history-save"),
    path("chat/history/<str:conv_id>/", views.delete_conversation, name="history-delete"),
]
