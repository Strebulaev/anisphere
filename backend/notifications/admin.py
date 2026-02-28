from django.contrib import admin
from .models import Complaint, Notification

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'complainant', 'complaint_type', 'reason', 'status', 'assigned_to', 'created_at')
    search_fields = ('complainant__username', 'reason', 'description')
    list_filter = ('complaint_type', 'reason', 'status', 'created_at', 'resolved_at')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    raw_id_fields = ('complainant', 'assigned_to')
    fieldsets = (
        ('Информация о жалобе', {
            'fields': ('content_type', 'object_id', 'complainant')
        }),
        ('Тип и причина', {
            'fields': ('complaint_type', 'reason', 'description')
        }),
        ('Статус', {
            'fields': ('status', 'assigned_to', 'resolution', 'resolved_at')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'title', 'content_object', 'is_read', 'is_deleted', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    list_filter = ('type', 'is_read', 'is_deleted', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)
    fieldsets = (
        ('Получатель', {
            'fields': ('user',)
        }),
        ('Тип и содержание', {
            'fields': ('type', 'title', 'content')
        }),
        ('Связанный объект', {
            'fields': ('content_type', 'object_id')
        }),
        ('Статус', {
            'fields': ('is_read', 'is_deleted')
        }),
        ('Дата', {
            'fields': ('created_at',)
        }),
    )