from rest_framework import serializers
from .models import Complaint, Notification, Reminder, NotificationSetting
from anime.serializers import AnimeSerializer


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_username = serializers.CharField(source='complainant.username', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complainant', 'complainant_username', 'complaint_type', 'reason',
            'description', 'status', 'assigned_to', 'resolution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'complainant', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'content', 'icon', 'link',
            'is_read', 'is_important', 'is_deleted',
            'created_at', 'read_at', 'expires_at',
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'is_deleted']


class ReminderSerializer(serializers.ModelSerializer):
    anime_detail = AnimeSerializer(source='anime', read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id', 'anime', 'anime_detail', 'reminder_time', 'repeat_weekly',
            'comment', 'is_active', 'is_triggered', 'created_at'
        ]
        read_only_fields = ['id', 'is_triggered', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReminderCreateSerializer(serializers.Serializer):
    anime_id = serializers.IntegerField()
    reminder_time = serializers.DateTimeField()
    repeat_weekly = serializers.BooleanField(default=False)
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = [
            'push_enabled', 'email_enabled', 'sound_enabled',
            'type_settings',
            'dnd_enabled', 'dnd_start', 'dnd_end',
            'auto_clean_read_days', 'auto_clean_unread_days',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
