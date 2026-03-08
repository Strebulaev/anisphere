from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, NotificationViewSet, ReminderViewSet, NotificationSettingViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'reminders', ReminderViewSet)

urlpatterns = router.urls + [
    # Настройки — без pk в URL
    path('settings/', NotificationSettingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update'})),
]
