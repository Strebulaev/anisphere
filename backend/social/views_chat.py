"""
Views для системы чатов согласно документации CHAT_SETTINGS.md
"""

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from django.utils.text import slugify
from django.core.cache import cache

from .models import (
    GroupChat, PrivateChat, ChatMember, ChatRole, Message,
    ChatAdminLog, MessageReadStatus, ChatFolder, ChatFolderChat
)
from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    SecurityLog, GroupChatSettings,
    PrivateChatSettings, MessagePin
)
from .serializers_chat import (
    ChatInviteLinkSerializer, ChatInviteLinkCreateSerializer,
    ChatWallpaperSerializer, ChatWallpaperPresetSerializer,
    ChatThemeSerializer,
    MessageReactionSerializer, MessageReactionCreateSerializer, GroupedReactionsSerializer,
    ChatBanSerializer, ChatBanCreateSerializer,
    ChatRestrictionSerializer, ChatRestrictionCreateSerializer,
    ChatSlowModeSerializer,
    ChatJoinRequestSerializer, ChatJoinRequestCreateSerializer,
    ChatTagSerializer, ChatTagAssignmentSerializer,
    AntiSpamRuleSerializer,
    ChatBackupSerializer,
    ScheduledMessageSerializer, ScheduledMessageCreateSerializer,
    GroupChatExtendedSerializer, PrivateChatExtendedSerializer,
    ChatFolderSerializer, ChatFolderCreateSerializer,
    SecurityLogSerializer, GroupChatSettingsSerializer,
    PrivateChatSettingsSerializer, MessagePinSerializer,
)
from .serializers import ChatRoleSerializer, MessageSerializer
from .services.chat_services import (
    PermissionChecker, SettingsCache, AntiSpamService,
    RateLimiter, SmartNotifications, ChatAnalytics,
    ChatBackupService, SettingsExport, NotificationService,
    permission_required, rate_limit, log_admin_action,
    settings_cache, rate_limiter, smart_notifications,
)
from users.models import User


# ==================== ССЫЛКИ-ПРИГЛАШЕНИЯ ====================

class ChatInviteLinkViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ссылками-приглашениями"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatInviteLink.objects.filter(
            Q(chat__members__user=self.request.user)
        ).select_related('chat', 'creator', 'auto_assign_role').distinct()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChatInviteLinkCreateSerializer
        return ChatInviteLinkSerializer
    
    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_invite_users', False):
                    raise PermissionDenied('У вас нет прав на создание приглашений')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Отозвать ссылку-приглашение"""
        invite_link = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=invite_link.chat, user=request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_invite_users', False):
                    raise PermissionDenied('У вас нет прав на отзыв приглашений')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        invite_link.is_revoked = True
        invite_link.save(update_fields=['is_revoked'])
        
        # Логируем
        ChatAdminLog.objects.create(
            chat=invite_link.chat,
            user=request.user,
            action='invite_link_revoked',
            details={'invite_link': invite_link.invite_link}
        )
        
        return Response({'status': 'revoked'})
    
    @action(detail=False, methods=['get'])
    def for_chat(self, request):
        """Получить все ссылки для конкретного чата"""
        chat_id = request.query_params.get('chat_id')
        if not chat_id:
            return Response({'error': 'chat_id required'}, status=400)
        
        links = self.get_queryset().filter(chat_id=chat_id, is_revoked=False)
        serializer = self.get_serializer(links, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_chat_by_invite(request, token):
    """Присоединиться к чату по ссылке-приглашению"""
    try:
        invite_link = ChatInviteLink.objects.select_related('chat').get(invite_link=token)
    except ChatInviteLink.DoesNotExist:
        return Response({'error': 'Ссылка не найдена'}, status=404)
    
    # Проверяем валидность
    if not invite_link.is_valid:
        return Response({'error': 'Ссылка недействительна'}, status=400)
    
    chat = invite_link.chat
    
    # Проверяем, не является ли пользователь уже участником
    if ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return Response({'error': 'Вы уже участник этого чата', 'chat_id': chat.id}, status=400)
    
    # Проверяем лимит участников
    if chat.members.count() >= chat.max_members:
        return Response({'error': 'Чат переполнен'}, status=400)
    
    # Создаём участника
    member = ChatMember.objects.create(
        user=request.user,
        chat=chat,
        role=invite_link.auto_assign_role,
        can_send_messages=chat.can_send_media,
        can_send_media=chat.can_send_media
    )
    
    # Увеличиваем счётчик использований
    invite_link.increment_usage()
    
    # Логируем
    ChatAdminLog.objects.create(
        chat=chat,
        user=request.user,
        action='member_joined',
        details={'invite_link': invite_link.invite_link}
    )
    
    return Response({
        'chat_id': chat.id,
        'chat_name': chat.name
    })


# ==================== ОБОИ ЧАТОВ ====================

class ChatWallpaperViewSet(viewsets.ModelViewSet):
    """ViewSet для управления обоями чатов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatWallpaperSerializer
    
    def get_queryset(self):
        queryset = ChatWallpaper.objects.filter(
            Q(user=self.request.user) | Q(is_preset=True)
        )
        
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def presets(self, request):
        """Получить предустановленные обои"""
        presets = ChatWallpaper.objects.filter(is_preset=True)
        serializer = self.get_serializer(presets, many=True)
        return Response(serializer.data)


@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def set_chat_wallpaper(request, chat_id):
    """Установить обои для чата"""
    chat_type = request.query_params.get('type', request.data.get('type', 'group'))  # group или private
    
    wallpaper_data = {
        'wallpaper_type': request.data.get('wallpaper_type', 'solid'),
        'wallpaper_color': request.data.get('wallpaper_color', '#1a1a1a'),
        'wallpaper_color2': request.data.get('wallpaper_color2', ''),
        'wallpaper_intensity': request.data.get('wallpaper_intensity', 100),
        'wallpaper_blur': request.data.get('wallpaper_blur', 0),
        'wallpaper_motion': request.data.get('wallpaper_motion', 'none'),
    }
    
    if chat_type == 'group':
        try:
            chat = GroupChat.objects.get(id=chat_id)
            
            # Проверяем права
            if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
                return Response({'error': 'Вы не участник этого чата'}, status=403)
            
            wallpaper, created = ChatWallpaper.objects.update_or_create(
                user=request.user,
                chat=chat,
                defaults=wallpaper_data
            )
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    else:  # private
        try:
            chat = PrivateChat.objects.get(
                Q(id=chat_id) & (Q(user1=request.user) | Q(user2=request.user))
            )
            
            wallpaper, created = ChatWallpaper.objects.update_or_create(
                user=request.user,
                private_chat=chat,
                defaults=wallpaper_data
            )
        except PrivateChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    return Response(ChatWallpaperSerializer(wallpaper, context={'request': request}).data)


# ==================== ТЕМЫ ОФОРМЛЕНИЯ ====================

class ChatThemeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления темами оформления"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatThemeSerializer
    
    def get_queryset(self):
        return ChatTheme.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==================== РЕАКЦИИ НА СООБЩЕНИЯ ====================

class MessageReactionViewSet(viewsets.ModelViewSet):
    """ViewSet для реакций на сообщения"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MessageReaction.objects.filter(
            Q(message__chat__members__user=self.request.user) |
            Q(message__private_chat__user1=self.request.user) |
            Q(message__private_chat__user2=self.request.user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageReactionCreateSerializer
        return MessageReactionSerializer
    
    def perform_create(self, serializer):
        message = serializer.validated_data['message']
        
        # Проверяем доступ к сообщению
        if message.chat:
            if not ChatMember.objects.filter(chat=message.chat, user=self.request.user).exists():
                raise PermissionDenied('Нет доступа к этому сообщению')
        elif message.private_chat:
            if message.private_chat.user1 != self.request.user and message.private_chat.user2 != self.request.user:
                raise PermissionDenied('Нет доступа к этому сообщению')
        
        result = serializer.save()
        if result is None:
            # Реакция была удалена (toggle)
            return Response({'status': 'removed'}, status=200)
    
    @action(detail=False, methods=['get'])
    def for_message(self, request):
        """Получить сгруппированные реакции для сообщения"""
        message_id = request.query_params.get('message_id')
        if not message_id:
            return Response({'error': 'message_id required'}, status=400)
        
        reactions = MessageReaction.objects.filter(
            message_id=message_id
        ).select_related('user')
        
        # Группируем реакции
        grouped = {}
        for reaction in reactions:
            emoji = reaction.emoji
            if emoji not in grouped:
                grouped[emoji] = {
                    'emoji': emoji,
                    'count': 0,
                    'users': [],
                    'is_mine': False
                }
            grouped[emoji]['count'] += 1
            grouped[emoji]['users'].append({
                'id': reaction.user.id,
                'username': reaction.user.username
            })
            if reaction.user == request.user:
                grouped[emoji]['is_mine'] = True
        
        return Response(list(grouped.values()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_reaction(request, message_id):
    """Добавить/удалить реакцию на сообщение"""
    emoji = request.data.get('emoji')
    if not emoji:
        return Response({'error': 'emoji required'}, status=400)
    
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)
    
    # Проверяем доступ
    if message.chat:
        if not ChatMember.objects.filter(chat=message.chat, user=request.user).exists():
            return Response({'error': 'Нет доступа'}, status=403)
    elif message.private_chat:
        if message.private_chat.user1 != request.user and message.private_chat.user2 != request.user:
            return Response({'error': 'Нет доступа'}, status=403)
    
    # Toggle реакции
    reaction, created = MessageReaction.objects.get_or_create(
        message=message,
        user=request.user,
        emoji=emoji
    )
    
    if not created:
        reaction.delete()
        return Response({'status': 'removed', 'emoji': emoji})
    
    return Response({'status': 'added', 'emoji': emoji})


# ==================== БЛОКИРОВКИ И ОГРАНИЧЕНИЯ ====================

class ChatBanViewSet(viewsets.ModelViewSet):
    """ViewSet для управления блокировками"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatBan.objects.filter(
            Q(chat__members__user=self.request.user)
        ).select_related('chat', 'user', 'banned_by').distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChatBanCreateSerializer
        return ChatBanSerializer
    
    def perform_create(self, serializer):
        serializer.save(banned_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        """Разблокировать пользователя"""
        ban = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=ban.chat, user=request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_ban_users', False):
                    raise PermissionDenied('У вас нет прав на разблокировку')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        ban.delete()
        
        # Логируем
        ChatAdminLog.objects.create(
            chat=ban.chat,
            user=request.user,
            action='member_unbanned',
            target_user=ban.user,
            details={'reason': 'Manual unban'}
        )
        
        return Response({'status': 'unbanned'})


class ChatRestrictionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ограничениями"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatRestriction.objects.filter(
            Q(chat__members__user=self.request.user)
        ).select_related('chat', 'user', 'restricted_by').distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRestrictionCreateSerializer
        return ChatRestrictionSerializer
    
    def perform_create(self, serializer):
        serializer.save(restricted_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def lift(self, request, pk=None):
        """Снять ограничение"""
        restriction = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=restriction.chat, user=request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_restrict_members', False):
                    raise PermissionDenied('У вас нет прав на снятие ограничений')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        restriction.delete()
        return Response({'status': 'lifted'})


# ==================== МЕДЛЕННЫЙ РЕЖИМ ====================

class ChatSlowModeViewSet(viewsets.ModelViewSet):
    """ViewSet для медленного режима"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSlowModeSerializer
    
    def get_queryset(self):
        return ChatSlowMode.objects.filter(
            chat__members__user=self.request.user
        )
    
    def perform_update(self, serializer):
        slow_mode = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=slow_mode.chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_manage_chat', False):
                    raise PermissionDenied('У вас нет прав на изменение настроек')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        serializer.save()


# ==================== ЗАПРОСЫ НА ВСТУПЛЕНИЕ ====================

class ChatJoinRequestViewSet(viewsets.ModelViewSet):
    """ViewSet для запросов на вступление"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatJoinRequest.objects.filter(
            Q(user=self.request.user) | Q(chat__members__user=self.request.user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChatJoinRequestCreateSerializer
        return ChatJoinRequestSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Одобрить запрос"""
        join_request = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=join_request.chat, user=request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_invite_users', False):
                    raise PermissionDenied('У вас нет прав на одобрение запросов')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        # Добавляем участника
        ChatMember.objects.create(
            user=join_request.user,
            chat=join_request.chat
        )
        
        # Обновляем статус запроса
        join_request.status = 'approved'
        join_request.reviewed_by = request.user
        join_request.reviewed_at = timezone.now()
        join_request.save()
        
        # Логируем
        ChatAdminLog.objects.create(
            chat=join_request.chat,
            user=request.user,
            action='member_joined',
            target_user=join_request.user,
            details={'method': 'join_request_approval'}
        )
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Отклонить запрос"""
        join_request = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=join_request.chat, user=request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_invite_users', False):
                    raise PermissionDenied('У вас нет прав на отклонение запросов')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        join_request.status = 'rejected'
        join_request.reviewed_by = request.user
        join_request.reviewed_at = timezone.now()
        join_request.save()
        
        return Response({'status': 'rejected'})


# ==================== ТЕГИ ЧАТОВ ====================

class ChatTagViewSet(viewsets.ModelViewSet):
    """ViewSet для тегов чатов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatTagSerializer
    
    def get_queryset(self):
        return ChatTag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatTagAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet для привязки тегов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatTagAssignmentSerializer
    
    def get_queryset(self):
        return ChatTagAssignment.objects.filter(tag__user=self.request.user)


# ==================== АНТИ-СПАМ ====================

class AntiSpamRuleViewSet(viewsets.ModelViewSet):
    """ViewSet для правил анти-спама"""
    permission_classes = [IsAuthenticated]
    serializer_class = AntiSpamRuleSerializer
    
    def get_queryset(self):
        return AntiSpamRule.objects.filter(
            chat__members__user=self.request.user
        )
    
    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_manage_chat', False):
                    raise PermissionDenied('У вас нет прав на создание правил')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        serializer.save()


# ==================== РЕЗЕРВНЫЕ КОПИИ ====================

class ChatBackupViewSet(viewsets.ModelViewSet):
    """ViewSet для резервных копий чатов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatBackupSerializer
    
    def get_queryset(self):
        return ChatBackup.objects.filter(
            Q(chat__members__user=self.request.user) | Q(created_by=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                raise PermissionDenied('Только администраторы могут создавать бэкапы')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Восстановить чат из резервной копии"""
        backup = self.get_object()
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=backup.chat, user=request.user)
            if not member.is_owner:
                raise PermissionDenied('Только владелец может восстанавливать бэкапы')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        # TODO: Реализовать логику восстановления
        return Response({'status': 'restoration_started'})


# ==================== ЗАПЛАНИРОВАННЫЕ СООБЩЕНИЯ ====================

class ScheduledMessageViewSet(viewsets.ModelViewSet):
    """ViewSet для запланированных сообщений"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledMessage.objects.filter(sender=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ScheduledMessageCreateSerializer
        return ScheduledMessageSerializer
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить запланированное сообщение"""
        message = self.get_object()
        
        if message.status != 'scheduled':
            return Response({'error': 'Можно отменить только запланированные сообщения'}, status=400)
        
        message.status = 'cancelled'
        message.save(update_fields=['status'])
        
        return Response({'status': 'cancelled'})
    
    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """Отправить запланированное сообщение сейчас"""
        message = self.get_object()
        
        if message.status != 'scheduled':
            return Response({'error': 'Можно отправить только запланированные сообщения'}, status=400)
        
        # TODO: Реализовать отправку сообщения
        message.status = 'sent'
        message.sent_at = timezone.now()
        message.save(update_fields=['status', 'sent_at'])
        
        return Response({'status': 'sent'})


# ==================== РОЛИ В ЧАТАХ ====================

class ChatRoleViewSet(viewsets.ModelViewSet):
    """ViewSet для ролей в чатах"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoleSerializer
    
    def get_queryset(self):
        return ChatRole.objects.filter(
            chat__members__user=self.request.user
        )
    
    def perform_create(self, serializer):
        chat_id = self.kwargs.get('chat_pk')
        chat = get_object_or_404(GroupChat, id=chat_id)
        
        # Проверяем права
        try:
            member = ChatMember.objects.get(chat=chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_add_new_admins', False):
                    raise PermissionDenied('У вас нет прав на создание ролей')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник этого чата')
        
        serializer.save(chat=chat, created_by=self.request.user)


# ==================== ДОПОЛНИТЕЛЬНЫЕ ДЕЙСТВИЯ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_member_role(request, chat_id, user_id):
    """Назначить роль участнику чата"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        target_member = ChatMember.objects.get(chat=chat, user_id=user_id)
        request_member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат или участник не найдены'}, status=404)
    
    # Нельзя менять роль владельца
    if target_member.is_owner:
        return Response({'error': 'Нельзя изменить роль владельца'}, status=400)
    
    # Проверяем права
    if not request_member.is_owner and not request_member.is_admin:
        if not request_member.effective_permissions.get('can_promote_members', False):
            return Response({'error': 'У вас нет прав на изменение ролей'}, status=403)
    
    # Нельзя повысить выше своего уровня
    role_id = request.data.get('role_id')
    if role_id:
        try:
            role = ChatRole.objects.get(id=role_id, chat=chat)
            if request_member.role and role.level >= request_member.role.level:
                if not request_member.is_owner:
                    return Response({'error': 'Нельзя назначить роль уровня выше или равного вашему'}, status=400)
        except ChatRole.DoesNotExist:
            return Response({'error': 'Роль не найдена'}, status=404)
    
    target_member.role_id = role_id
    target_member.save(update_fields=['role_id'])
    
    # Логируем
    ChatAdminLog.objects.create(
        chat=chat,
        user=request.user,
        action='member_promoted' if role_id else 'member_demoted',
        target_user=target_member.user,
        details={'new_role_id': role_id}
    )
    
    return Response({'status': 'role_updated'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_ownership(request, chat_id):
    """Передать владение чатом"""
    new_owner_id = request.data.get('user_id')
    if not new_owner_id:
        return Response({'error': 'user_id required'}, status=400)
    
    try:
        chat = GroupChat.objects.get(id=chat_id)
        current_owner_member = ChatMember.objects.get(chat=chat, user=request.user)
        new_owner_member = ChatMember.objects.get(chat=chat, user_id=new_owner_id)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат или участник не найдены'}, status=404)
    
    # Только владелец может передать владение
    if not current_owner_member.is_owner:
        return Response({'error': 'Только владелец может передать владение'}, status=403)
    
    with transaction.atomic():
        # Снимаем владельца
        chat.created_by = new_owner_member.user
        chat.save(update_fields=['created_by'])
        
        # Обновляем роли
        current_owner_member.is_admin = True
        current_owner_member.save(update_fields=['is_admin'])
        
        new_owner_member.is_admin = True
        new_owner_member.save(update_fields=['is_admin'])
        
        # Логируем
        ChatAdminLog.objects.create(
            chat=chat,
            user=request.user,
            action='chat_updated',
            target_user=new_owner_member.user,
            details={'action': 'ownership_transferred'}
        )
    
    return Response({'status': 'ownership_transferred'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_banned_users(request, chat_id):
    """Получить список заблокированных пользователей"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем права
    if not member.is_owner and not member.is_admin:
        if not member.effective_permissions.get('can_ban_users', False):
            return Response({'error': 'Нет доступа'}, status=403)
    
    bans = ChatBan.objects.filter(chat=chat).select_related('user', 'banned_by')
    serializer = ChatBanSerializer(bans, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_restricted_users(request, chat_id):
    """Получить список ограниченных пользователей"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем права
    if not member.is_owner and not member.is_admin:
        if not member.effective_permissions.get('can_restrict_members', False):
            return Response({'error': 'Нет доступа'}, status=403)
    
    restrictions = ChatRestriction.objects.filter(
        chat=chat
    ).filter(
        Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
    ).select_related('user', 'restricted_by')
    
    serializer = ChatRestrictionSerializer(restrictions, many=True)
    return Response(serializer.data)


# ==================== ПАПКИ ЧАТОВ ====================

class ChatFolderViewSet(viewsets.ModelViewSet):
    """ViewSet для управления папками чатов"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user).prefetch_related('chats')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChatFolderCreateSerializer
        return ChatFolderSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Изменить порядок папок"""
        folder_ids = request.data.get('folder_ids', [])
        
        if not folder_ids:
            return Response({'error': 'folder_ids required'}, status=400)
        
        with transaction.atomic():
            for index, folder_id in enumerate(folder_ids):
                ChatFolder.objects.filter(
                    id=folder_id,
                    user=request.user
                ).update(order=index)
        
        return Response({'status': 'reordered'})
    
    @action(detail=True, methods=['post'])
    def add_chat(self, request, pk=None):
        """Добавить чат в папку"""
        folder = self.get_object()
        chat_id = request.data.get('chat_id')
        chat_type = request.data.get('chat_type', 'group')
        
        if not chat_id:
            return Response({'error': 'chat_id required'}, status=400)
        
        if chat_type == 'group':
            try:
                chat = GroupChat.objects.get(id=chat_id)
                ChatFolderChat.objects.get_or_create(
                    folder=folder,
                    group_chat=chat
                )
            except GroupChat.DoesNotExist:
                return Response({'error': 'Чат не найден'}, status=404)
        else:
            try:
                chat = PrivateChat.objects.filter(
                    id=chat_id
                ).filter(
                    Q(user1=request.user) | Q(user2=request.user)
                ).first()
                if not chat:
                    return Response({'error': 'Чат не найден'}, status=404)
                ChatFolderChat.objects.get_or_create(
                    folder=folder,
                    private_chat=chat
                )
            except Exception:
                return Response({'error': 'Чат не найден'}, status=404)
        
        return Response({'status': 'added'})
    
    @action(detail=True, methods=['post'])
    def remove_chat(self, request, pk=None):
        """Удалить чат из папки"""
        folder = self.get_object()
        chat_id = request.data.get('chat_id')
        chat_type = request.data.get('chat_type', 'group')
        
        if not chat_id:
            return Response({'error': 'chat_id required'}, status=400)
        
        if chat_type == 'group':
            ChatFolderChat.objects.filter(
                folder=folder,
                group_chat_id=chat_id
            ).delete()
        else:
            ChatFolderChat.objects.filter(
                folder=folder,
                private_chat_id=chat_id
            ).delete()
        
        return Response({'status': 'removed'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folder_chats(request, folder_id):
    """Получить чаты в папке"""
    try:
        folder = ChatFolder.objects.get(id=folder_id, user=request.user)
    except ChatFolder.DoesNotExist:
        return Response({'error': 'Папка не найдена'}, status=404)
    
    chats_data = []
    
    # Получаем явно добавленные чаты
    for chat_in_folder in folder.chats.all():
        if chat_in_folder.group_chat:
            chat = chat_in_folder.group_chat
            chats_data.append({
                'id': chat.id,
                'type': 'group',
                'name': chat.name,
                'avatar_url': chat.avatar.url if chat.avatar else None,
            })
        elif chat_in_folder.private_chat:
            chat = chat_in_folder.private_chat
            other = chat.other_user(request.user)
            chats_data.append({
                'id': chat.id,
                'type': 'private',
                'name': other.display_name or other.username,
                'avatar_url': other.avatar.url if other.avatar else None,
            })
    
    # Применяем автоматические правила если включены
    if folder.include_private or folder.include_groups:
        # TODO: Реализовать автоматическое добавление по правилам
        pass
    
    return Response(chats_data)


# ==================== ЖУРНАЛ БЕЗОПАСНОСТИ ====================

class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра журнала безопасности"""
    permission_classes = [IsAuthenticated]
    serializer_class = SecurityLogSerializer
    
    def get_queryset(self):
        queryset = SecurityLog.objects.filter(user=self.request.user)
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        is_suspicious = self.request.query_params.get('is_suspicious')
        if is_suspicious:
            queryset = queryset.filter(is_suspicious=is_suspicious.lower() == 'true')
        
        return queryset.order_by('-created_at')


# ==================== АНАЛИТИКА ЧАТА ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request, chat_id):
    """Получить аналитику чата"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Только админы могут видеть аналитику
    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)
    
    analytics = ChatAnalytics(chat)
    days = int(request.query_params.get('days', 7))
    
    data = {
        'activity': analytics.get_activity_stats(days),
        'members': analytics.get_member_stats(),
        'content': analytics.get_content_stats(days),
        'engagement_score': analytics.get_engagement_score(),
    }
    
    return Response(data)


# ==================== ЭКСПОРТ/ИМПОРТ НАСТРОЕК ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_settings(request):
    """Экспорт настроек пользователя"""
    exporter = SettingsExport()
    data = exporter.export_user_settings(request.user)
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_settings(request):
    """Импорт настроек пользователя"""
    importer = SettingsExport()
    result = importer.import_user_settings(request.user, request.data)
    return Response(result)


# ==================== МАССОВЫЕ ОПЕРАЦИИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_delete_messages(request, chat_id):
    """Массовое удаление сообщений"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем права
    checker = PermissionChecker(request.user, chat)
    result = checker.has_permission('can_delete_messages')
    if not result.allowed:
        return Response({'error': result.reason}, status=403)
    
    message_ids = request.data.get('message_ids', [])
    if not message_ids:
        return Response({'error': 'message_ids required'}, status=400)
    
    # Удаляем сообщения
    deleted_count = Message.objects.filter(
        id__in=message_ids,
        chat=chat
    ).update(
        is_deleted=True,
        deleted_at=timezone.now(),
        deleted_by=request.user
    )
    
    # Логируем
    ChatAdminLog.objects.create(
        chat=chat,
        user=request.user,
        action='message_deleted',
        details={'count': deleted_count, 'message_ids': message_ids[:10]}
    )
    
    return Response({'deleted_count': deleted_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_add_members(request, chat_id):
    """Массовое добавление участников"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем права
    checker = PermissionChecker(request.user, chat)
    result = checker.has_permission('can_invite_users')
    if not result.allowed:
        return Response({'error': result.reason}, status=403)
    
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': 'user_ids required'}, status=400)
    
    # Проверяем лимит участников
    current_count = chat.members.count()
    if current_count + len(user_ids) > chat.max_members:
        return Response({'error': 'Превышен лимит участников'}, status=400)
    
    # Добавляем участников
    added_count = 0
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            # Проверяем, не является ли уже участником
            if not ChatMember.objects.filter(chat=chat, user=user).exists():
                ChatMember.objects.create(
                    user=user,
                    chat=chat,
                    can_send_messages=chat.can_send_media,
                    can_send_media=chat.can_send_media
                )
                added_count += 1
        except User.DoesNotExist:
            continue
    
    # Логируем
    ChatAdminLog.objects.create(
        chat=chat,
        user=request.user,
        action='member_joined',
        details={'count': added_count, 'method': 'bulk_add'}
    )
    
    return Response({'added_count': added_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_remove_members(request, chat_id):
    """Массовое удаление участников"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем права
    checker = PermissionChecker(request.user, chat)
    result = checker.has_permission('can_manage_chat')
    if not result.allowed:
        return Response({'error': result.reason}, status=403)
    
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': 'user_ids required'}, status=400)
    
    # Нельзя удалить владельца
    if chat.created_by_id in user_ids:
        return Response({'error': 'Нельзя удалить владельца'}, status=400)
    
    # Удаляем участников
    removed_count = ChatMember.objects.filter(
        chat=chat,
        user_id__in=user_ids
    ).delete()[0]
    
    # Логируем
    ChatAdminLog.objects.create(
        chat=chat,
        user=request.user,
        action='member_left',
        details={'count': removed_count, 'method': 'bulk_remove'}
    )
    
    return Response({'removed_count': removed_count})


# ==================== УПРАВЛЕНИЕ СООБЩЕНИЯМИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_message_new(request, message_id):
    """Закрепить сообщение (новая реализация)"""
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)
    
    # Определяем чат
    chat = message.chat or message.private_chat
    if not chat:
        return Response({'error': 'Сообщение не привязано к чату'}, status=400)
    
    # Проверяем права
    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        result = checker.has_permission('can_pin_messages')
        if not result.allowed:
            return Response({'error': result.reason}, status=403)
    
    # Проверяем, не закреплено ли уже
    if hasattr(message, 'pin_info'):
        return Response({'error': 'Сообщение уже закреплено'}, status=400)
    
    # Закрепляем
    pin = MessagePin.objects.create(
        chat=message.chat,
        private_chat=message.private_chat,
        message=message,
        pinned_by=request.user
    )
    
    # Обновляем флаг в сообщении
    message.is_pinned = True
    message.pinned_by = request.user
    message.pinned_at = timezone.now()
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])
    
    # Логируем для группового чата
    if message.chat:
        ChatAdminLog.objects.create(
            chat=message.chat,
            user=request.user,
            action='message_pinned',
            message=message
        )
    
    return Response(MessagePinSerializer(pin).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_message_new(request, message_id):
    """Открепить сообщение (новая реализация)"""
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)
    
    # Проверяем права
    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        result = checker.has_permission('can_pin_messages')
        if not result.allowed:
            return Response({'error': result.reason}, status=403)
    
    # Удаляем запись о закреплении
    MessagePin.objects.filter(message=message).delete()
    
    # Обновляем флаг в сообщении
    message.is_pinned = False
    message.pinned_by = None
    message.pinned_at = None
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])
    
    # Логируем для группового чата
    if message.chat:
        ChatAdminLog.objects.create(
            chat=message.chat,
            user=request.user,
            action='message_unpinned',
            message=message
        )
    
    return Response({'status': 'unpinned'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pinned_messages_new(request, chat_id):
    """Получить закреплённые сообщения чата"""
    chat_type = request.query_params.get('type', 'group')
    
    if chat_type == 'group':
        try:
            chat = GroupChat.objects.get(id=chat_id)
            if not chat.members.filter(user=request.user).exists():
                return Response({'error': 'Нет доступа'}, status=403)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
        
        pins = MessagePin.objects.filter(chat=chat).select_related('message', 'pinned_by')
    else:
        try:
            chat = PrivateChat.objects.filter(
                id=chat_id
            ).filter(
                Q(user1=request.user) | Q(user2=request.user)
            ).first()
            if not chat:
                return Response({'error': 'Чат не найден'}, status=404)
        except Exception:
            return Response({'error': 'Чат не найден'}, status=404)
        
        pins = MessagePin.objects.filter(private_chat=chat).select_related('message', 'pinned_by')
    
    serializer = MessagePinSerializer(pins, many=True)
    return Response(serializer.data)


# ==================== АНТИ-СПАМ ПРОВЕРКА ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_message_spam(request, chat_id):
    """Проверить сообщение на спам (для превью)"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
    except GroupChat.DoesNotExist:
        return Response({'error': 'Чат не найден'}, status=404)
    
    # Создаём временный объект сообщения для проверки
    text = request.data.get('text', '')
    media = request.data.get('media')
    
    temp_message = Message(
        chat=chat,
        sender=request.user,
        text=text,
        media=media
    )
    
    # Проверяем
    anti_spam = AntiSpamService(chat)
    result = anti_spam.check_message(temp_message)
    
    return Response(result)


# ==================== ОЧИСТКА ЧАТА ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_chat_history(request, chat_id):
    """Очистить историю чата (только для себя в личных чатах)"""
    chat_type = request.query_params.get('type', 'private')
    
    if chat_type == 'private':
        try:
            chat = PrivateChat.objects.filter(
                id=chat_id
            ).filter(
                Q(user1=request.user) | Q(user2=request.user)
            ).first()
            if not chat:
                return Response({'error': 'Чат не найден'}, status=404)
        except Exception:
            return Response({'error': 'Чат не найден'}, status=404)
        
        # В личных чатах просто удаляем статус прочтения
        # Сообщения остаются, но пользователь их не видит
        MessageReadStatus.objects.filter(
            message__private_chat=chat,
            user=request.user
        ).delete()
        
        return Response({'status': 'cleared'})
    
    else:
        # Для групповых чатов - только владелец может очистить
        try:
            chat = GroupChat.objects.get(id=chat_id)
            member = ChatMember.objects.get(chat=chat, user=request.user)
        except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
            return Response({'error': 'Чат не найден'}, status=404)
        
        if not member.is_owner:
            return Response({'error': 'Только владелец может очистить чат'}, status=403)
        
        # Удаляем все сообщения
        deleted_count = Message.objects.filter(chat=chat).update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=request.user
        )
        
        # Логируем
        ChatAdminLog.objects.create(
            chat=chat,
            user=request.user,
            action='chat_updated',
            details={'action': 'clear_history', 'deleted_count': deleted_count}
        )
        
        return Response({'status': 'cleared', 'deleted_count': deleted_count})
