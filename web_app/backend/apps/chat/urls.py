from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat, name="chat"),
    path("chat/info/", views.info, name="chat-info"),
    path("chat/conversations/", views.list_conversations, name="conv-list"),
    path("chat/conversations/<str:conv_id>/", views.get_conversation_detail, name="conv-detail"),
    path("chat/save_conversation/", views.save_conversation, name="conv-save"),
    path("chat/delete_conversation/<str:conv_id>/", views.delete_conversation, name="conv-delete"),
]
