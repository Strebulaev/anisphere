from rest_framework import serializers
from .models import Complaint, Notification


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
            'id', 'type', 'title', 'content', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']