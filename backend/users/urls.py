from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profile-settings', views.UserProfileSettingsViewSet, basename='profile-settings')
router.register(r'notification-settings', views.NotificationSettingsViewSet, basename='notification-settings')
router.register(r'privacy-settings', views.PrivacySettingsViewSet, basename='privacy-settings')
router.register(r'themes', views.UserThemeViewSet, basename='themes')
router.register(r'chat-backgrounds', views.ChatBackgroundViewSet, basename='chat-backgrounds')
router.register(r'analytics', views.UserAnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
    # JWT токены
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Социальная аутентификация
    path('google/', views.GoogleAuthView.as_view(), name='google_auth'),
    path('google/callback/', views.GoogleAuthCallbackView.as_view(), name='google_auth_callback'),

    # Верификация
    path('verify/phone/', views.PhoneVerificationView.as_view(), name='phone_verification'),
    path('verify/email/', views.EmailVerificationView.as_view(), name='email_verification'),
    path('confirm-email/', views.EmailConfirmView.as_view(), name='email_confirm'),

    # Профиль
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),

    # Сброс пароля
    path('password-reset/', views.password_reset, name='password_reset'),

    # Обновление профиля
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),

    # Настройки
    path('settings/', views.UserSettingsView.as_view(), name='user_settings'),

    # Сессии
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    path('sessions/<int:pk>/', views.UserSessionDetailView.as_view(), name='user_session_detail'),

    # Проверка nickname
    path('nickname/check/', views.NicknameCheckView.as_view(), name='nickname_check'),

    # Двухфакторная аутентификация
    path('2fa/status/', views.TwoFactorAuthViewSet.as_view({'get': 'status'}), name='two_factor_status'),
    path('2fa/enable/', views.TwoFactorAuthViewSet.as_view({'post': 'enable'}), name='two_factor_enable'),
    path('2fa/verify/', views.TwoFactorAuthViewSet.as_view({'post': 'verify'}), name='two_factor_verify'),
    path('2fa/backup-codes/', views.TwoFactorAuthViewSet.as_view({'get': 'backup_codes', 'post': 'regenerate_backup_codes'}), name='two_factor_backup_codes'),
    path('2fa/disable/', views.TwoFactorAuthViewSet.as_view({'post': 'disable'}), name='two_factor_disable'),

    # Пользователи онлайн
    path('online/', views.OnlineUsersView.as_view(), name='online_users'),

    # Обновления в реальном времени
    path('realtime/', views.RealtimeUpdatesView.as_view(), name='realtime_updates'),

    # Поиск пользователей
    path('search/', views.UserSearchView.as_view(), name='user_search'),
]