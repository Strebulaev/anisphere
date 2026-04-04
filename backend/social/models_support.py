"""
Модели для мини-чата поддержки (обращения к админам)
"""
from django.db import models
from django.conf import settings


class SupportTicket(models.Model):
    """Обращение пользователя в поддержку"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('answered', 'Есть ответ'),
        ('closed', 'Закрыто'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='social_support_tickets'
    )
    subject = models.CharField(max_length=200, blank=True, default='Обращение в поддержку')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Связанное аниме (опционально)
    anime_id = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Обращение #{self.id} от {self.user.username}"
    
    @property
    def is_open(self):
        return self.status != 'closed'
    
    def get_other_user(self, user):
        """Получить собеседника (для пользователя - админ, для админа - пользователь)"""
        if user.is_staff or user.is_superuser:
            return self.user
        return None


class SupportMessage(models.Model):
    """Сообщение в обращении поддержки"""
    
    ticket = models.ForeignKey(
        SupportTicket, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='social_support_messages'
    )
    text = models.TextField()
    
    # Для отслеживания прочтения
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"Сообщение от {self.sender.username} в тикете #{self.ticket.id}"
