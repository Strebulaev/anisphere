"""
Views для системы настроек чатов: обои, темы, роли, модерация, папки.
Объединяет функциональность views.py и views_chat.py.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from django.core.cache import cache

from .models import (
    GroupChat, PrivateChat, ChatMember, ChatRole, Message,
    ChatAdminLog, MessageReadStatus, ChatFolder, ChatFolderChat
)
from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    SecurityLog, GroupChatSettings, PrivateChatSettings, MessagePin,
    GroupMemberSettings,
)
from .services.chat_settings_service import (
    ChatSettingsService, PermissionChecker, SettingsCache,
    NotificationService, RateLimiter, AntiSpamService,
    SettingsExport, SettingsVersioning, PermissionResult,
)
from users.models import User


# ==================== НАСТРОЙКИ ЧАТА (ОБОИ + ТЕМА) ====================

class ChatCustomizationViewSet(viewsets.ViewSet):
    """API для кастомизации чата: обои, тема, шрифты, цвета"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _check_chat_access(self, request, chat_type: str, chat_id: int):
        """Проверить доступ к чату"""
        if chat_type == 'group':
            chat = get_object_or_404(GroupChat, id=chat_id)
            if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
                raise PermissionDenied("Вы не участник этого чата")
            return chat
        else:
            chat = PrivateChat.objects.filter(
                id=chat_id
            ).filter(Q(user1=request.user) | Q(user2=request.user)).first()
            if not chat:
                raise PermissionDenied("Чат не найден или нет доступа")
            return chat

    # ==================== ОБОИ ====================

    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper')
    def get_wallpaper(self, request, chat_type=None, chat_id=None):
        """Получить обои чата"""
        self._check_chat_access(request, chat_type, int(chat_id))
        data = ChatSettingsService.get_wallpaper_for_chat(request.user, chat_type, int(chat_id))
        if not data:
            return Response({'wallpaper': None})
        return Response({'wallpaper': data})

    @action(detail=False, methods=['put', 'post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/set')
    def set_wallpaper(self, request, chat_type=None, chat_id=None):
        """Установить обои для чата"""
        self._check_chat_access(request, chat_type, int(chat_id))

        # Загрузка изображения
        if 'wallpaper_image' in request.FILES:
            file = request.FILES['wallpaper_image']
            if file.size > 5 * 1024 * 1024:
                return Response({'error': 'Файл слишком большой (максимум 5MB)'}, status=400)

            from .models_chat import ChatWallpaper as WP
            defaults = {
                'wallpaper_type': 'image',
                'wallpaper_image': file,
                'wallpaper_blur': request.data.get('wallpaper_blur', 0),
                'wallpaper_intensity': request.data.get('wallpaper_intensity', 100),
                'wallpaper_color': '#000000',
            }
            if chat_type == 'group':
                wp, _ = WP.objects.update_or_create(user=request.user, chat_id=chat_id, defaults=defaults)
            else:
                wp, _ = WP.objects.update_or_create(user=request.user, private_chat_id=chat_id, defaults=defaults)

            SettingsCache.invalidate(request.user.id, chat_type, int(chat_id))
            return Response({
                'wallpaper': ChatSettingsService._wallpaper_to_dict(wp),
                'message': 'Обои установлены'
            })

        # Цвет/градиент/паттерн
        data = ChatSettingsService.set_wallpaper_for_chat(request.user, chat_type, int(chat_id), request.data)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'wallpaper': data, 'message': 'Обои установлены'})

    @action(detail=False, methods=['delete'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/reset')
    def reset_wallpaper(self, request, chat_type=None, chat_id=None):
        """Сбросить обои"""
        self._check_chat_access(request, chat_type, int(chat_id))
        ChatSettingsService.reset_wallpaper(request.user, chat_type, int(chat_id))
        return Response({'message': 'Обои сброшены'})

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/wallpaper/preset')
    def apply_wallpaper_preset(self, request, chat_type=None, chat_id=None):
        """Применить предустановленные обои"""
        self._check_chat_access(request, chat_type, int(chat_id))
        preset_id = request.data.get('preset_id')
        if not preset_id:
            return Response({'error': 'preset_id required'}, status=400)
        data = ChatSettingsService.apply_preset_wallpaper(request.user, chat_type, int(chat_id), preset_id)
        if not data:
            return Response({'error': 'Пресет не найден'}, status=404)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'wallpaper': data, 'message': 'Обои применены'})

    @action(detail=False, methods=['get'], url_path='wallpapers/presets')
    def wallpaper_presets(self, request):
        """Список предустановленных обоев"""
        presets = ChatSettingsService.PRESET_WALLPAPERS
        # Группируем по категориям
        categories = {}
        for p in presets:
            cat = p.get('preset_category') or p.get('category', 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)
        return Response({'presets': presets, 'categories': categories})

    # ==================== ТЕМЫ ====================

    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme')
    def get_theme(self, request, chat_type=None, chat_id=None):
        """Получить тему чата"""
        self._check_chat_access(request, chat_type, int(chat_id))
        data = ChatSettingsService.get_theme_for_chat(request.user, chat_type, int(chat_id))
        return Response({'theme': data or ChatSettingsService._default_theme()})

    @action(detail=False, methods=['put', 'post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/set')
    def set_theme(self, request, chat_type=None, chat_id=None):
        """Установить тему чата"""
        self._check_chat_access(request, chat_type, int(chat_id))
        data = ChatSettingsService.set_theme_for_chat(request.user, chat_type, int(chat_id), request.data)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'theme': data, 'message': 'Тема применена'})

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/preset')
    def apply_theme_preset(self, request, chat_type=None, chat_id=None):
        """Применить предустановленную тему"""
        self._check_chat_access(request, chat_type, int(chat_id))
        preset_id = request.data.get('preset_id')
        if not preset_id:
            return Response({'error': 'preset_id required'}, status=400)
        data = ChatSettingsService.apply_preset_theme(request.user, chat_type, int(chat_id), preset_id)
        if not data:
            return Response({'error': 'Тема не найдена'}, status=404)
        SettingsVersioning.increment_version(request.user.id)
        return Response({'theme': data, 'message': 'Тема применена'})

    @action(detail=False, methods=['get'], url_path='themes/presets')
    def theme_presets(self, request):
        """Список предустановленных тем"""
        return Response({'presets': ChatSettingsService.PRESET_THEMES})

    @action(detail=False, methods=['delete'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/theme/reset')
    def reset_theme(self, request, chat_type=None, chat_id=None):
        """Сбросить тему к дефолтной"""
        self._check_chat_access(request, chat_type, int(chat_id))
        from .models_chat import ChatTheme as CT
        if chat_type == 'group':
            CT.objects.filter(user=request.user, chat_id=chat_id).delete()
        else:
            CT.objects.filter(user=request.user, private_chat_id=chat_id).delete()
        SettingsCache.invalidate(request.user.id, chat_type, int(chat_id))
        return Response({'message': 'Тема сброшена', 'theme': ChatSettingsService._default_theme()})

    # ==================== ВСЕ НАСТРОЙКИ СРАЗУ ====================

    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/all')
    def get_all_settings(self, request, chat_type=None, chat_id=None):
        """Получить все настройки чата сразу (обои + тема + CSS переменные)"""
        self._check_chat_access(request, chat_type, int(chat_id))
        data = ChatSettingsService.get_all_settings_for_chat(request.user, chat_type, int(chat_id))
        return Response(data)

    @action(detail=False, methods=['post'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/bulk-update')
    def bulk_update_settings(self, request, chat_type=None, chat_id=None):
        """Массовое обновление настроек (обои + тема за один запрос)"""
        self._check_chat_access(request, chat_type, int(chat_id))

        result = {}

        if 'wallpaper' in request.data:
            wp_data = request.data['wallpaper']
            if wp_data:
                result['wallpaper'] = ChatSettingsService.set_wallpaper_for_chat(
                    request.user, chat_type, int(chat_id), wp_data
                )

        if 'theme' in request.data:
            theme_data = request.data['theme']
            if theme_data:
                result['theme'] = ChatSettingsService.set_theme_for_chat(
                    request.user, chat_type, int(chat_id), theme_data
                )

        SettingsVersioning.increment_version(request.user.id)
        SettingsCache.invalidate(request.user.id, chat_type, int(chat_id))
        result['css_vars'] = ChatSettingsService._build_css_vars(
            result.get('wallpaper'),
            result.get('theme')
        )
        return Response({'settings': result, 'message': 'Настройки сохранены'})

    # ==================== CSS ПЕРЕМЕННЫЕ ====================

    @action(detail=False, methods=['get'], url_path='(?P<chat_type>group|private)/(?P<chat_id>[0-9]+)/css-vars')
    def get_css_vars(self, request, chat_type=None, chat_id=None):
        """Получить CSS-переменные для применения в браузере"""
        self._check_chat_access(request, chat_type, int(chat_id))
        wallpaper = ChatSettingsService.get_wallpaper_for_chat(request.user, chat_type, int(chat_id))
        theme = ChatSettingsService.get_theme_for_chat(request.user, chat_type, int(chat_id))
        css_vars = ChatSettingsService._build_css_vars(wallpaper, theme)

        # Генерируем CSS строку
        css_string = ':root {\n' + '\n'.join(f'  {k}: {v};' for k, v in css_vars.items()) + '\n}'
        return Response({'css_vars': css_vars, 'css_string': css_string})


# ==================== НАСТРОЙКИ ЛИЧНОГО ЧАТА ====================

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def private_chat_user_settings(request, chat_id):
    """Получить/обновить персональные настройки личного чата"""
    chat = get_object_or_404(PrivateChat, id=chat_id)

    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, created = PrivateChatSettings.objects.get_or_create(
        chat=chat, user=request.user
    )

    if request.method == 'GET':
        return Response(_serialize_private_settings(settings_obj, request))

    # PUT/PATCH — обновление
    data = request.data
    updatable = [
        'custom_name', 'notifications_enabled', 'sound_enabled',
        'notification_sound', 'vibration_enabled', 'show_preview',
        'show_popup', 'muted_until', 'is_archived', 'is_pinned',
        'is_hidden', 'auto_delete_enabled', 'auto_delete_after',
        'folder_id', 'tags',
    ]
    for field in updatable:
        if field in data:
            setattr(settings_obj, field, data[field])

    # Блокировка
    if 'is_blocked' in data:
        settings_obj.is_blocked = data['is_blocked']
        if data['is_blocked']:
            settings_obj.blocked_at = timezone.now()

    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    SettingsVersioning.increment_version(request.user.id)

    return Response({
        'settings': _serialize_private_settings(settings_obj, request),
        'message': 'Настройки сохранены'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mute_private_chat(request, chat_id):
    """Заглушить личный чат"""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    duration = request.data.get('duration')  # минуты, None = навсегда
    settings_obj, _ = PrivateChatSettings.objects.get_or_create(chat=chat, user=request.user)

    if duration is None:
        settings_obj.muted_until = None  # навсегда
        settings_obj.notifications_enabled = False
    else:
        settings_obj.muted_until = timezone.now() + timezone.timedelta(minutes=int(duration))

    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)

    return Response({'message': 'Чат заглушен', 'muted_until': settings_obj.muted_until})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unmute_private_chat(request, chat_id):
    """Включить уведомления в личном чате"""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = PrivateChatSettings.objects.get_or_create(chat=chat, user=request.user)
    settings_obj.muted_until = None
    settings_obj.notifications_enabled = True
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Уведомления включены'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def block_user_in_private_chat(request, chat_id):
    """Заблокировать пользователя в личном чате"""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = PrivateChatSettings.objects.get_or_create(chat=chat, user=request.user)
    settings_obj.is_blocked = True
    settings_obj.blocked_at = timezone.now()
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Пользователь заблокирован'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unblock_user_in_private_chat(request, chat_id):
    """Разблокировать пользователя в личном чате"""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа'}, status=403)

    settings_obj, _ = PrivateChatSettings.objects.get_or_create(chat=chat, user=request.user)
    settings_obj.is_blocked = False
    settings_obj.blocked_at = None
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'private', chat_id)
    return Response({'message': 'Пользователь разблокирован'})


def _serialize_private_settings(settings_obj, request) -> dict:
    return {
        'id': settings_obj.id,
        'chat_id': settings_obj.chat_id,
        'custom_name': settings_obj.custom_name,
        'custom_avatar_url': request.build_absolute_uri(settings_obj.custom_avatar.url) if settings_obj.custom_avatar else None,
        'notifications_enabled': settings_obj.notifications_enabled,
        'sound_enabled': settings_obj.sound_enabled,
        'notification_sound': settings_obj.notification_sound,
        'vibration_enabled': settings_obj.vibration_enabled,
        'show_preview': settings_obj.show_preview,
        'show_popup': settings_obj.show_popup,
        'muted_until': settings_obj.muted_until,
        'is_muted': settings_obj.is_muted,
        'is_archived': settings_obj.is_archived,
        'is_pinned': settings_obj.is_pinned,
        'is_hidden': settings_obj.is_hidden,
        'is_blocked': settings_obj.is_blocked,
        'blocked_at': settings_obj.blocked_at,
        'auto_delete_enabled': settings_obj.auto_delete_enabled,
        'auto_delete_after': settings_obj.auto_delete_after,
        'folder_id': settings_obj.folder_id,
        'tags': settings_obj.tags,
        'updated_at': settings_obj.updated_at,
    }


# ==================== НАСТРОЙКИ УЧАСТНИКА ГРУППЫ ====================

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def group_member_settings(request, chat_id):
    """Персональные настройки участника группового чата"""
    chat = get_object_or_404(GroupChat, id=chat_id)
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)

    if request.method == 'GET':
        return Response({
            'notifications_enabled': settings_obj.notifications_enabled,
            'mentions_only': settings_obj.mentions_only,
            'sound_enabled': settings_obj.sound_enabled,
            'show_preview': settings_obj.show_preview,
            'muted_until': settings_obj.muted_until,
            'is_muted': settings_obj.is_muted,
            'is_pinned': settings_obj.is_pinned,
            'is_archived': settings_obj.is_archived,
            'tags': settings_obj.tags,
        })

    updatable = [
        'notifications_enabled', 'mentions_only', 'sound_enabled',
        'show_preview', 'muted_until', 'is_pinned', 'is_archived', 'tags'
    ]
    for field in updatable:
        if field in request.data:
            setattr(settings_obj, field, request.data[field])
    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'group', chat_id)

    return Response({'message': 'Настройки сохранены'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mute_group_chat(request, chat_id):
    """Заглушить группу"""
    chat = get_object_or_404(GroupChat, id=chat_id)
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if not member:
        return Response({'error': 'Вы не участник'}, status=403)

    settings_obj, _ = GroupMemberSettings.objects.get_or_create(membership=member)
    duration = request.data.get('duration')

    if duration is None:
        settings_obj.notifications_enabled = False
        settings_obj.muted_until = None
    else:
        settings_obj.muted_until = timezone.now() + timezone.timedelta(minutes=int(duration))

    settings_obj.save()
    SettingsCache.invalidate(request.user.id, 'group', chat_id)
    return Response({'message': 'Группа заглушена'})


# ==================== ССЫЛКИ-ПРИГЛАШЕНИЯ ====================

class ChatInviteLinkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatInviteLink.objects.filter(
            chat__members__user=self.request.user
        ).select_related('chat', 'creator').distinct()

    def get_serializer_class(self):
        from .serializers_chat import ChatInviteLinkSerializer, ChatInviteLinkCreateSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ChatInviteLinkCreateSerializer
        return ChatInviteLinkSerializer

    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        try:
            member = ChatMember.objects.get(chat=chat, user=self.request.user)
            if not member.is_owner and not member.is_admin:
                if not member.effective_permissions.get('can_invite_users', False):
                    raise PermissionDenied('Нет прав на создание приглашений')
        except ChatMember.DoesNotExist:
            raise PermissionDenied('Вы не участник чата')
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        invite = self.get_object()
        invite.is_revoked = True
        invite.save(update_fields=['is_revoked'])
        ChatAdminLog.objects.create(
            chat=invite.chat, user=request.user,
            action='invite_link_revoked',
            details={'invite_link': invite.invite_link}
        )
        return Response({'status': 'revoked'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_chat_by_invite(request, token):
    """Присоединиться к чату по ссылке"""
    try:
        invite = ChatInviteLink.objects.select_related('chat').get(invite_link=token)
    except ChatInviteLink.DoesNotExist:
        return Response({'error': 'Ссылка не найдена'}, status=404)

    if not invite.is_valid:
        return Response({'error': 'Ссылка недействительна'}, status=400)

    chat = invite.chat
    if ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return Response({'error': 'Вы уже участник', 'chat_id': chat.id}, status=400)

    if chat.members.count() >= chat.max_members:
        return Response({'error': 'Чат переполнен'}, status=400)

    ChatMember.objects.create(
        user=request.user,
        chat=chat,
        role=invite.auto_assign_role
    )
    invite.increment_usage()

    ChatAdminLog.objects.create(
        chat=chat, user=request.user,
        action='member_joined',
        details={'invite_link': invite.invite_link}
    )

    return Response({'chat_id': chat.id, 'chat_name': chat.name})


# ==================== БЛОКИРОВКИ И ОГРАНИЧЕНИЯ ====================

class ChatBanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatBan.objects.filter(
            chat__members__user=self.request.user
        ).select_related('chat', 'user', 'banned_by').distinct()

    def get_serializer_class(self):
        from .serializers_chat import ChatBanSerializer, ChatBanCreateSerializer
        return ChatBanCreateSerializer if self.action == 'create' else ChatBanSerializer

    def perform_create(self, serializer):
        serializer.save(banned_by=self.request.user)

    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        ban = self.get_object()
        member = ChatMember.objects.filter(chat=ban.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав на разблокировку')
        ban.delete()
        ChatAdminLog.objects.create(
            chat=ban.chat, user=request.user,
            action='member_unbanned', target_user=ban.user,
            details={'reason': 'Manual unban'}
        )
        return Response({'status': 'unbanned'})


class ChatRestrictionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatRestriction.objects.filter(
            chat__members__user=self.request.user
        ).select_related('chat', 'user', 'restricted_by').distinct()

    def get_serializer_class(self):
        from .serializers_chat import ChatRestrictionSerializer, ChatRestrictionCreateSerializer
        return ChatRestrictionCreateSerializer if self.action == 'create' else ChatRestrictionSerializer

    def perform_create(self, serializer):
        serializer.save(restricted_by=self.request.user)

    @action(detail=True, methods=['post'])
    def lift(self, request, pk=None):
        restriction = self.get_object()
        member = ChatMember.objects.filter(chat=restriction.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав на снятие ограничений')
        restriction.delete()
        return Response({'status': 'lifted'})


# ==================== РОЛИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_member_role(request, chat_id, user_id):
    """Назначить роль участнику"""
    try:
        chat = GroupChat.objects.get(id=chat_id)
        target_member = ChatMember.objects.get(chat=chat, user_id=user_id)
        request_member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if target_member.is_owner:
        return Response({'error': 'Нельзя изменить роль владельца'}, status=400)

    if not request_member.is_owner and not request_member.is_admin:
        checker = PermissionChecker(request.user, chat)
        result = checker.has_permission('can_promote_members')
        if not result.allowed:
            return Response({'error': result.reason}, status=403)

    role_id = request.data.get('role_id')
    if role_id:
        try:
            role = ChatRole.objects.get(id=role_id, chat=chat)
        except ChatRole.DoesNotExist:
            return Response({'error': 'Роль не найдена'}, status=404)
        target_member.role = role
    else:
        target_member.role = None

    target_member.save(update_fields=['role'])

    ChatAdminLog.objects.create(
        chat=chat, user=request.user,
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
        current_member = ChatMember.objects.get(chat=chat, user=request.user)
        new_member = ChatMember.objects.get(chat=chat, user_id=new_owner_id)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not current_member.is_owner:
        return Response({'error': 'Только владелец может передать владение'}, status=403)

    with transaction.atomic():
        chat.created_by = new_member.user
        chat.save(update_fields=['created_by'])
        current_member.is_admin = True
        current_member.save(update_fields=['is_admin'])
        new_member.is_admin = True
        new_member.save(update_fields=['is_admin'])

        ChatAdminLog.objects.create(
            chat=chat, user=request.user,
            action='chat_updated', target_user=new_member.user,
            details={'action': 'ownership_transferred'}
        )

    return Response({'status': 'ownership_transferred'})


# ==================== ЗАБАНЕННЫЕ И ОГРАНИЧЕННЫЕ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_banned_users(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)

    from .serializers_chat import ChatBanSerializer
    bans = ChatBan.objects.filter(chat=chat).select_related('user', 'banned_by')
    return Response(ChatBanSerializer(bans, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_restricted_users(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)

    from .serializers_chat import ChatRestrictionSerializer
    restrictions = ChatRestriction.objects.filter(chat=chat).filter(
        Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
    ).select_related('user', 'restricted_by')
    return Response(ChatRestrictionSerializer(restrictions, many=True).data)


# ==================== РЕАКЦИИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_reaction(request, message_id):
    """Добавить/убрать реакцию"""
    emoji = request.data.get('emoji')
    if not emoji:
        return Response({'error': 'emoji required'}, status=400)

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        if not ChatMember.objects.filter(chat=message.chat, user=request.user).exists():
            return Response({'error': 'Нет доступа'}, status=403)
    elif message.private_chat:
        if request.user not in [message.private_chat.user1, message.private_chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)

    reaction, created = MessageReaction.objects.get_or_create(
        message=message, user=request.user, emoji=emoji
    )
    if not created:
        reaction.delete()
        return Response({'status': 'removed', 'emoji': emoji})
    return Response({'status': 'added', 'emoji': emoji})


# ==================== ПАПКИ ЧАТОВ ====================

class ChatFolderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        from .serializers_chat import ChatFolderSerializer, ChatFolderCreateSerializer
        return ChatFolderCreateSerializer if self.action in ['create', 'update', 'partial_update'] else ChatFolderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        folder_ids = request.data.get('folder_ids', [])
        with transaction.atomic():
            for i, fid in enumerate(folder_ids):
                ChatFolder.objects.filter(id=fid, user=request.user).update(order=i)
        return Response({'status': 'reordered'})

    @action(detail=True, methods=['post'])
    def add_chat(self, request, pk=None):
        folder = self.get_object()
        chat_id = request.data.get('chat_id')
        chat_type = request.data.get('chat_type', 'group')
        if not chat_id:
            return Response({'error': 'chat_id required'}, status=400)
        if chat_type == 'group':
            ChatFolderChat.objects.get_or_create(folder=folder, group_chat_id=chat_id)
        else:
            ChatFolderChat.objects.get_or_create(folder=folder, private_chat_id=chat_id)
        return Response({'status': 'added'})

    @action(detail=True, methods=['post'])
    def remove_chat(self, request, pk=None):
        folder = self.get_object()
        chat_id = request.data.get('chat_id')
        chat_type = request.data.get('chat_type', 'group')
        if chat_type == 'group':
            ChatFolderChat.objects.filter(folder=folder, group_chat_id=chat_id).delete()
        else:
            ChatFolderChat.objects.filter(folder=folder, private_chat_id=chat_id).delete()
        return Response({'status': 'removed'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folder_chats(request, folder_id):
    folder = get_object_or_404(ChatFolder, id=folder_id, user=request.user)
    chats_data = []
    for item in folder.chats.all():
        if item.group_chat:
            c = item.group_chat
            chats_data.append({
                'id': c.id, 'type': 'group', 'name': c.name,
                'avatar_url': c.avatar.url if c.avatar else None
            })
        elif item.private_chat:
            c = item.private_chat
            other = c.other_user(request.user)
            chats_data.append({
                'id': c.id, 'type': 'private', 'name': other.display_name or other.username,
                'avatar_url': other.avatar.url if other.avatar else None
            })
    return Response(chats_data)


# ==================== АНАЛИТИКА ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_analytics(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    if not member.is_owner and not member.is_admin:
        return Response({'error': 'Нет доступа'}, status=403)

    analytics = AntiSpamService(chat)
    from .services.chat_settings_service import ChatAnalytics as CA
    ca = CA(chat)
    days = int(request.query_params.get('days', 7))
    return Response({
        'activity': ca.get_activity_stats(days),
        'members': ca.get_member_stats(),
        'content': ca.get_content_stats(days),
        'engagement_score': ca.get_engagement_score(),
    })


# ==================== ЭКСПОРТ/ИМПОРТ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_settings(request):
    exporter = SettingsExport()
    return Response(exporter.export_user_settings(request.user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_settings(request):
    importer = SettingsExport()
    return Response(importer.import_user_settings(request.user, request.data))


# ==================== МАССОВЫЕ ОПЕРАЦИИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_delete_messages(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    checker = PermissionChecker(request.user, chat)
    r = checker.has_permission('can_delete_messages')
    if not r.allowed:
        return Response({'error': r.reason}, status=403)

    ids = request.data.get('message_ids', [])
    count = Message.objects.filter(id__in=ids, chat=chat).update(
        is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user
    )
    return Response({'deleted_count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_add_members(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    checker = PermissionChecker(request.user, chat)
    r = checker.has_permission('can_invite_users')
    if not r.allowed:
        return Response({'error': r.reason}, status=403)

    user_ids = request.data.get('user_ids', [])
    added = 0
    for uid in user_ids:
        try:
            u = User.objects.get(id=uid)
            if not ChatMember.objects.filter(chat=chat, user=u).exists():
                ChatMember.objects.create(user=u, chat=chat)
                added += 1
        except User.DoesNotExist:
            continue
    return Response({'added_count': added})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_remove_members(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        member = ChatMember.objects.get(chat=chat, user=request.user)
    except (GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        return Response({'error': 'Не найдено'}, status=404)

    checker = PermissionChecker(request.user, chat)
    r = checker.has_permission('can_manage_chat')
    if not r.allowed:
        return Response({'error': r.reason}, status=403)

    ids = request.data.get('user_ids', [])
    if chat.created_by_id in ids:
        return Response({'error': 'Нельзя удалить владельца'}, status=400)
    count = ChatMember.objects.filter(chat=chat, user_id__in=ids).delete()[0]
    return Response({'removed_count': count})


# ==================== ЗАКРЕПЛЕНИЕ СООБЩЕНИЙ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_message_new(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        r = checker.has_permission('can_pin_messages')
        if not r.allowed:
            return Response({'error': r.reason}, status=403)

    MessagePin.objects.get_or_create(
        chat=message.chat,
        private_chat=message.private_chat,
        message=message,
        defaults={'pinned_by': request.user}
    )
    message.is_pinned = True
    message.pinned_by = request.user
    message.pinned_at = timezone.now()
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])

    if message.chat:
        ChatAdminLog.objects.create(
            chat=message.chat, user=request.user,
            action='message_pinned', message=message
        )
    return Response({'status': 'pinned'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_message_new(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Сообщение не найдено'}, status=404)

    if message.chat:
        checker = PermissionChecker(request.user, message.chat)
        r = checker.has_permission('can_pin_messages')
        if not r.allowed:
            return Response({'error': r.reason}, status=403)

    MessagePin.objects.filter(message=message).delete()
    message.is_pinned = False
    message.pinned_by = None
    message.pinned_at = None
    message.save(update_fields=['is_pinned', 'pinned_by', 'pinned_at'])
    return Response({'status': 'unpinned'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pinned_messages_new(request, chat_id):
    chat_type = request.query_params.get('type', 'group')
    if chat_type == 'group':
        chat = get_object_or_404(GroupChat, id=chat_id)
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'error': 'Нет доступа'}, status=403)
        pins = MessagePin.objects.filter(chat=chat).select_related('message', 'pinned_by')
    else:
        chat = get_object_or_404(PrivateChat, id=chat_id)
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)
        pins = MessagePin.objects.filter(private_chat=chat).select_related('message', 'pinned_by')

    data = [{'id': p.id, 'message_id': p.message_id, 'pinned_by': p.pinned_by.username, 'created_at': p.created_at} for p in pins]
    return Response(data)


# ==================== ОЧИСТКА ИСТОРИИ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_chat_history(request, chat_id):
    chat_type = request.query_params.get('type', 'private')
    if chat_type == 'private':
        chat = get_object_or_404(PrivateChat, id=chat_id)
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа'}, status=403)
        # Личный чат: очищаем только для себя
        MessageReadStatus.objects.filter(message__private_chat=chat, user=request.user).delete()
        return Response({'status': 'cleared'})
    else:
        chat = get_object_or_404(GroupChat, id=chat_id)
        member = ChatMember.objects.filter(chat=chat, user=request.user).first()
        if not member or not member.is_owner:
            return Response({'error': 'Только владелец может очистить чат'}, status=403)
        count = Message.objects.filter(chat=chat).update(
            is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user
        )
        return Response({'status': 'cleared', 'deleted_count': count})


# ==================== ЖУРНАЛ БЕЗОПАСНОСТИ ====================

class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SecurityLog.objects.filter(user=self.request.user)
        action = self.request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        from .serializers_chat import SecurityLogSerializer
        return SecurityLogSerializer


# ==================== ЗАПРОСЫ НА ВСТУПЛЕНИЕ ====================

class ChatJoinRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatJoinRequest.objects.filter(
            Q(user=self.request.user) | Q(chat__members__user=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        from .serializers_chat import ChatJoinRequestSerializer, ChatJoinRequestCreateSerializer
        return ChatJoinRequestCreateSerializer if self.action == 'create' else ChatJoinRequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        jr = self.get_object()
        member = ChatMember.objects.filter(chat=jr.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав')
        ChatMember.objects.create(user=jr.user, chat=jr.chat)
        jr.status = 'approved'
        jr.reviewed_by = request.user
        jr.reviewed_at = timezone.now()
        jr.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        jr = self.get_object()
        member = ChatMember.objects.filter(chat=jr.chat, user=request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Нет прав')
        jr.status = 'rejected'
        jr.reviewed_by = request.user
        jr.reviewed_at = timezone.now()
        jr.save()
        return Response({'status': 'rejected'})


# ==================== ТЕГИ ====================

class ChatTagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatTag.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        from .serializers_chat import ChatTagSerializer
        return ChatTagSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==================== АНТИ-СПАМ ====================

class AntiSpamRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AntiSpamRule.objects.filter(chat__members__user=self.request.user)

    def get_serializer_class(self):
        from .serializers_chat import AntiSpamRuleSerializer
        return AntiSpamRuleSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_message_spam(request, chat_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
    except GroupChat.DoesNotExist:
        return Response({'error': 'Чат не найден'}, status=404)

    text = request.data.get('text', '')
    temp = Message(chat=chat, sender=request.user, text=text)
    service = AntiSpamService(chat)
    return Response(service.check_message(temp))


# ==================== ЗАПЛАНИРОВАННЫЕ СООБЩЕНИЯ ====================

class ScheduledMessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScheduledMessage.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        from .serializers_chat import ScheduledMessageSerializer, ScheduledMessageCreateSerializer
        return ScheduledMessageCreateSerializer if self.action in ['create', 'update', 'partial_update'] else ScheduledMessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        msg = self.get_object()
        if msg.status != 'scheduled':
            return Response({'error': 'Можно отменить только запланированные'}, status=400)
        msg.status = 'cancelled'
        msg.save(update_fields=['status'])
        return Response({'status': 'cancelled'})


# ==================== РЕЗЕРВНЫЕ КОПИИ ====================

class ChatBackupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatBackup.objects.filter(
            Q(chat__members__user=self.request.user) | Q(created_by=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        from .serializers_chat import ChatBackupSerializer
        return ChatBackupSerializer

    def perform_create(self, serializer):
        chat = serializer.validated_data.get('chat')
        member = ChatMember.objects.filter(chat=chat, user=self.request.user).first()
        if not member or (not member.is_owner and not member.is_admin):
            raise PermissionDenied('Только администраторы')
        serializer.save(created_by=self.request.user)
