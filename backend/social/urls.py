# social/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommentListCreateView, CommentDetailView, GroupViewSet,
    PostViewSet, MessageListCreateView, CombinedChatsView,
    GroupChatViewSet, ChatRoleViewSet, PrivateChatViewSet, MessageViewSet,
    get_chat_detail, CreateGroupChatView,
    PrivateChatSettingsView, GroupChatSettingsView, ChatSettingsListView
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'posts', PostViewSet)
router.register(r'group-chats', GroupChatViewSet)
router.register(r'group-chats/(?P<chat_pk>\d+)/roles', ChatRoleViewSet, basename='chat-roles')
router.register(r'private-chats', PrivateChatViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('chats/', CombinedChatsView.as_view(), name='combined-chats'),
    path('chats/<int:pk>/', get_chat_detail, name='chat-detail'),
    path('chats/<int:pk>/settings/', get_chat_detail, name='chat-settings'),
    path('group-chats/create/', CreateGroupChatView.as_view(), name='create-group-chat'),
    path('private-chats/<int:chat_id>/settings/', PrivateChatSettingsView.as_view(), name='private-chat-settings'),
    path('group-chats/<int:chat_id>/settings/', GroupChatSettingsView.as_view(), name='group-chat-settings'),
    path('chat-settings/', ChatSettingsListView.as_view(), name='chat-settings-list'),
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
] + router.urls