from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status, mixins
from django.utils import timezone
from datetime import timedelta

from .models import Complaint, Notification, Reminder, NotificationSetting
from .serializers import (
    ComplaintSerializer, NotificationSerializer,
    ReminderSerializer, ReminderCreateSerializer,
    NotificationSettingSerializer,
)
from anime.models import Anime


class ComplaintViewSet(ModelViewSet):
    queryset = Complaint.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        return self.queryset.filter(complainant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(complainant=self.request.user)


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = self.queryset.filter(
            user=self.request.user,
            is_deleted=False,
        ).order_by('-created_at')

        # Фильтр по типу
        ntype = self.request.query_params.get('type')
        if ntype:
            qs = qs.filter(type=ntype)

        # Фильтр только непрочитанных
        unread = self.request.query_params.get('unread')
        if unread in ('1', 'true'):
            qs = qs.filter(is_read=False)

        # Только важные
        important = self.request.query_params.get('important')
        if important in ('1', 'true'):
            qs = qs.filter(is_important=True)

        return qs

    # ── Мягкое удаление ──────────────────────────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_deleted = True
        notification.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Дополнительные эндпоинты ──────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """GET /api/notifications/notifications/count/ — количество непрочитанных"""
        cnt = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
        ).count()
        return Response({'count': cnt})

    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        """GET /api/notifications/notifications/recent/ — последние 8 для дропдауна"""
        try:
            qs = Notification.objects.filter(
                user=request.user,
                is_deleted=False,
            ).order_by('-created_at')[:8]
            serializer = self.get_serializer(qs, many=True)
            unread_count = Notification.objects.filter(
                user=request.user, is_read=False, is_deleted=False
            ).count()
            return Response({
                'results': serializer.data,
                'unread_count': unread_count,
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in notifications/recent: {e}", exc_info=True)
            return Response({
                'results': [],
                'unread_count': 0,
                'error': 'Failed to load notifications'
            }, status=500)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """POST /api/notifications/notifications/{id}/mark_read/"""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response({
            'status': 'ok',
            'id': notification.id,
            'is_read': True,
        })

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        """POST /api/notifications/notifications/mark_all_read/"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'status': 'ok', 'count': count})

    @action(detail=True, methods=['post'], url_path='toggle_important')
    def toggle_important(self, request, pk=None):
        """POST /api/notifications/notifications/{id}/toggle_important/"""
        notification = self.get_object()
        notification.is_important = not notification.is_important
        notification.save(update_fields=['is_important'])
        return Response({
            'status': 'ok',
            'id': notification.id,
            'is_important': notification.is_important,
        })

    @action(detail=False, methods=['delete'], url_path='clean')
    def clean(self, request):
        """DELETE /api/notifications/notifications/clean/ — удалить прочитанные"""
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True,
            is_important=False,
        ).update(is_deleted=True), None
        return Response({'status': 'ok'})

    @action(detail=False, methods=['delete'], url_path='delete_all')
    def delete_all(self, request):
        """DELETE /api/notifications/notifications/delete_all/ — удалить все (кроме важных)"""
        Notification.objects.filter(
            user=request.user,
            is_important=False,
        ).update(is_deleted=True)
        return Response({'status': 'ok'})


class ReminderViewSet(ModelViewSet):
    queryset = Reminder.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ReminderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = ReminderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        anime_id = serializer.validated_data['anime_id']
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)

        reminder = Reminder.objects.create(
            user=request.user,
            anime=anime,
            reminder_time=serializer.validated_data['reminder_time'],
            repeat_weekly=serializer.validated_data.get('repeat_weekly', False),
            comment=serializer.validated_data.get('comment', ''),
        )
        return Response(ReminderSerializer(reminder).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_active = False
        reminder.save(update_fields=['is_active'])
        return Response({'status': 'deactivated'})

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """GET /api/notifications/reminders/upcoming/ — напоминания в ближайший час"""
        now = timezone.now()
        reminders = self.get_queryset().filter(
            is_active=True,
            reminder_time__gte=now - timedelta(minutes=1),
            reminder_time__lte=now + timedelta(minutes=60),
        ).order_by('reminder_time')[:20]
        return Response(ReminderSerializer(reminders, many=True).data)


class NotificationSettingViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """GET/PUT /api/notifications/settings/"""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSettingSerializer

    def get_object(self):
        obj, _ = NotificationSetting.objects.get_or_create(user=self.request.user)
        return obj

    # Переопределяем retrieve, чтобы не нужен был pk в URL
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
