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
router.register(r'library', views.UserLibraryViewSet, basename='library')

urlpatterns = [
    path('', include(router.urls)),
    
    # Текущий пользователь (должен быть ПЕРЕД router.urls)
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    
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
    path('profile/<int:pk>/', views.UserPublicProfileView.as_view(), name='user_public_profile'),

    # Сброс пароля
    path('password-reset/', views.password_reset, name='password_reset'),

    # Обновление профиля
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),

    # Настройки
    path('settings/', views.UserSettingsView.as_view(), name='user_settings'),

    # Объединенные настройки с Redis кешированием
    # path('settings/all/', views.AllSettingsView.as_view(), name='all_settings'),
    # path('settings/cache/clear/', views.AllSettingsView.as_view({'post': 'clear_cache'}), name='clear_settings_cache'),

    # Загрузка аватара
    path('avatar/', views.AvatarUploadView.as_view(), name='avatar_upload'),

    # Смена пароля
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Сессии
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    path('sessions/<int:pk>/', views.UserSessionDetailView.as_view(), name='user_session_detail'),

    # Проверка nickname
    path('nickname/check/', views.NicknameCheckView.as_view(), name='nickname_check'),

    # Двухфакторная аутентификация
    path('2fa/status/', views.TwoFactorAuthViewSet.as_view({'get': 'status'}), name='two_factor_status'),
    path('2fa/enable/', views.TwoFactorAuthViewSet.as_view({'post': 'enable'}), name='two_factor_enable'),
    path('2fa/verify/', views.TwoFactorAuthViewSet.as_view({'post': 'verify'}), name='two_factor_verify'),
    path('2fa/verify-backup/', views.TwoFactorAuthViewSet.as_view({'post': 'verify_backup_code'}), name='two_factor_verify_backup'),
    path('2fa/backup-codes/', views.TwoFactorAuthViewSet.as_view({'get': 'backup_codes', 'post': 'regenerate_backup_codes'}), name='two_factor_backup_codes'),
    path('2fa/disable/', views.TwoFactorAuthViewSet.as_view({'post': 'disable'}), name='two_factor_disable'),
    path('2fa/settings/', views.TwoFactorAuthViewSet.as_view({'post': 'update_settings'}), name='two_factor_settings'),
    path('2fa/security-log/', views.TwoFactorAuthViewSet.as_view({'get': 'security_log'}), name='two_factor_security_log'),

    # Активные сессии
    path('sessions/active/', views.SessionViewSet.as_view({'get': 'list'}), name='active_sessions'),
    path('sessions/terminate/', views.SessionViewSet.as_view({'post': 'terminate'}), name='terminate_session'),
    path('sessions/terminate-all/', views.SessionViewSet.as_view({'post': 'terminate_all_others'}), name='terminate_all_sessions'),

    # Удаление аккаунта
    path('account-deletion/', views.AccountDeletionView.as_view(), name='account_deletion'),
    # path('cancel-deletion/', views.AccountDeletionView.as_view({'delete': 'delete'}), name='cancel_deletion'),

    # Настройки темы
    path('theme-settings/', views.ThemeSettingsView.as_view(), name='theme_settings'),

    # Настройки фона чатов
    path('chat-background-settings/', views.ChatBackgroundSettingsView.as_view(), name='chat_background_settings'),

    # Настройки шрифтов
    path('font-settings/', views.FontSettingsView.as_view(), name='font_settings'),

    # Использование памяти
    path('storage-usage/', views.StorageUsageView.as_view(), name='storage_usage'),

    # Синхронизация
    path('sync-settings/', views.SyncSettingsView.as_view(), name='sync_settings'),

    # Экспорт данных
    path('export-data/', views.ExportDataView.as_view(), name='export_data'),

    # Очистка кэша
    path('clear-cache/', views.ClearCacheView.as_view(), name='clear_cache'),

    # Пользователи онлайн
    path('online/', views.OnlineUsersView.as_view(), name='online_users'),

    # Обновления в реальном времени
    path('realtime/', views.RealtimeUpdatesView.as_view(), name='realtime_updates'),

    # Поиск пользователей
    path('search/', views.UserSearchView.as_view(), name='user_search'),

    # Отладка аутентификации
    path('headers-debug/', views.HeadersDebugView.as_view(), name='headers_debug'),
    path('auth-debug/', views.AuthDebugView.as_view(), name='auth_debug'),

    # Лента пользователя
    path('<int:user_id>/feed/', views.UserFeedView.as_view(), name='user_feed'),

    # Статистика пользователя (по ID или username)
    path('<int:pk>/stats/', views.UserStatsView.as_view(), name='user_stats'),
    path('<str:pk>/stats/', views.UserStatsView.as_view(), name='user_stats_by_username'),

    # Объединенные настройки (раскомментировано)
    path('settings/all/', views.AllSettingsView.as_view(), name='all_settings'),
    # path('settings/cache/clear/', ...),  # Удалён - теперь используется PUT для обновления настроек

    # Список пользователей с фильтрацией по статусу
    path('users/', views.UsersListView.as_view(), name='users_list'),
]