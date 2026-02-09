from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User

class Complaint(models.Model):
    """Жалобы на контент"""

    COMPLAINT_TYPES = [
        ('playlist', 'Плейлист'),
        ('playlist_item', 'Элемент плейлиста'),
        ('comment', 'Комментарий'),
        ('reactor_post', 'Reactor пост'),
        ('group', 'Группа'),
        ('dub', 'Озвучка'),
        ('user', 'Пользователь'),
    ]

    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('harassment', 'Харассмент'),
        ('inappropriate', 'Неподходящий контент'),
        ('copyright', 'Нарушение авторских прав'),
        ('misleading', 'Вводящая в заблуждение информация'),
        ('broken_link', 'Битая ссылка'),
        ('duplicate', 'Дубликат'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('investigating', 'Расследуется'),
        ('resolved', 'Решена'),
        ('dismissed', 'Отклонена'),
    ]

    # Полиморфная связь с объектом жалобы
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Автор жалобы
    complainant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')

    # Детали жалобы
    complaint_type = models.CharField(max_length=20, choices=COMPLAINT_TYPES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)

    # Статус и обработка
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolution = models.TextField(blank=True)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Complaint by {self.complainant.username} on {self.content_object}"


class Notification(models.Model):
    """Уведомления пользователей"""

    NOTIFICATION_TYPES = [
        ('comment', 'Комментарий'),
        ('like', 'Лайк'),
        ('follow', 'Подписка'),
        ('mention', 'Упоминание'),
        ('group_invite', 'Приглашение в группу'),
        ('contest', 'Конкурс'),
        ('message', 'Сообщение'),
        ('system', 'Системное'),
    ]

    # Получатель
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    # Тип и контент
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()

    # Полиморфная связь с объектом уведомления (опционально)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Статус
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
