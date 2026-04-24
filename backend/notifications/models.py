from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from users.models import User
from anime.models import Anime


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

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    complainant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')

    complaint_type = models.CharField(max_length=20, choices=COMPLAINT_TYPES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolution = models.TextField(blank=True)

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
        return f"Complaint by {self.complainant.username}"


class Notification(models.Model):
    """Уведомления пользователей"""

    NOTIFICATION_TYPES = [
        # Социальные
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
        ('heart', 'Сердечко'),
        ('comment', 'Комментарий'),
        ('reply', 'Ответ на комментарий'),
        ('mention', 'Упоминание'),
        ('follow', 'Подписка'),
        ('repost', 'Репост'),
        # Контент / группы
        ('message', 'Сообщение'),
        ('group_message', 'Сообщение в группе'),
        ('group_invite', 'Приглашение в группу'),
        # Достижения и конкурсы
        ('achievement', 'Достижение'),
        ('contest', 'Новый конкурс'),
        ('contest_vote', 'Голосование'),
        ('contest_results', 'Результаты конкурса'),
        ('contest_win', 'Победа в конкурсе'),
        # Напоминания
        ('reminder_episode', 'Напоминание о серии'),
        ('reminder_event', 'Напоминание о событии'),
        ('reminder_contest', 'Напоминание о конкурсе'),
        # Системные
        ('system', 'Системное'),
        ('warning', 'Предупреждение'),
        ('security', 'Безопасность'),
    ]

    # Получатель
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    # Тип и данные
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    link = models.CharField(max_length=500, blank=True)

    # Полиморфная связь с объектом уведомления (опционально)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Статусы
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'is_deleted', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class Reminder(models.Model):
    """Напоминание о выходе новых серий аниме"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='reminders')

    reminder_time = models.DateTimeField(verbose_name='Время напоминания')
    repeat_weekly = models.BooleanField(default=False, verbose_name='Повторять еженедельно')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    # Настройки уведомлений для этого напоминания
    enable_sound = models.BooleanField(default=True, verbose_name='Звук уведомления')
    enable_push = models.BooleanField(default=True, verbose_name='Пуш-уведомление')

    is_active = models.BooleanField(default=True, verbose_name='Активно')
    is_triggered = models.BooleanField(default=False, verbose_name='Сработало')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reminder_time']
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['anime', 'is_active']),
            models.Index(fields=['reminder_time', 'is_active']),
        ]
        unique_together = ['user', 'anime', 'reminder_time']

    def __str__(self):
        return f"Reminder for {self.user.username}: {self.anime.title_ru}"


class NotificationSetting(models.Model):
    """Настройки уведомлений пользователя"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notif_settings')

    # Типы — JSON с настройками для каждого типа
    type_settings = models.JSONField(default=dict)

    # Каналы
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    # Режим "Не беспокоить"
    dnd_enabled = models.BooleanField(default=False)
    dnd_start = models.TimeField(null=True, blank=True)
    dnd_end = models.TimeField(null=True, blank=True)

    # Автоочистка
    auto_clean_read_days = models.IntegerField(default=30)
    auto_clean_unread_days = models.IntegerField(default=90)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки уведомлений'

    def __str__(self):
        return f"NotificationSettings for {self.user.username}"
