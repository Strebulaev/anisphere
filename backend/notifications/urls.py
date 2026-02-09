from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = router.urls