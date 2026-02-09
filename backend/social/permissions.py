from rest_framework import permissions
from .models import ChatMember

class IsChatOwner(permissions.BasePermission):
    """Проверка, является ли пользователь владельцем чата"""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'chat'):
            return obj.chat.created_by == request.user
        return False


class HasChatPermission(permissions.BasePermission):
    """Проверка наличия конкретного разрешения в чате"""

    def __init__(self, permission):
        self.permission = permission

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Для объектов GroupChat
        if hasattr(obj, 'members'):
            try:
                member = obj.members.get(user=request.user)
                return member.effective_permissions.get(self.permission, False)
            except ChatMember.DoesNotExist:
                return False

        # Для других объектов (например, сообщения)
        elif hasattr(obj, 'chat'):
            try:
                member = obj.chat.members.get(user=request.user)
                return member.effective_permissions.get(self.permission, False)
            except ChatMember.DoesNotExist:
                return False

        return False


class IsChatMember(permissions.BasePermission):
    """Проверка, является ли пользователь участником чата"""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Для объектов GroupChat
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user).exists()

        # Для других объектов (например, сообщения)
        elif hasattr(obj, 'chat'):
            return obj.chat.members.filter(user=request.user).exists()

        return False