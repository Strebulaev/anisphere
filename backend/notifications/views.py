from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from .models import Complaint, Notification
from .serializers import ComplaintSerializer, NotificationSerializer


class ComplaintViewSet(ModelViewSet):
    queryset = Complaint.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        # Пользователи видят только свои жалобы
        return self.queryset.filter(complainant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(complainant=self.request.user)


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # Пользователи видят только свои уведомления
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
