from django.utils import timezone
from django.contrib.sessions.models import Session
from users.models import UserSession
from core.online_status import online_status, publish_user_online_event
import logging

logger = logging.getLogger(__name__)

class OnlineStatusMiddleware:
    """Middleware для отслеживания онлайн статуса пользователей через Redis"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

            # Обновляем статус онлайн в Redis (быстро, без блокировок)
            online_status.set_online(
                user.id,
                user.username,
                extra_data={'display_name': user.display_name or user.username}
            )

            # Обновляем last_seen в БД (асинхронно не блокируя запрос)
            # Это нужно для fallback если Redis недоступен
            try:
                user.last_seen = timezone.now()
                user.save(update_fields=['last_seen'])
            except Exception:
                pass  # Игнорируем ошибки БД

            # Публикуем событие для WebSocket подписчиков
            publish_user_online_event(user.id, user.username)

            # Обновляем сессию пользователя
            self.update_user_session(request, user)

        return response

    def update_user_session(self, request, user):
        """Обновление сессии пользователя"""
        session_key = request.session.session_key
        if session_key:
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

            device_info = 'Unknown Device'
            if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                device_info = 'Mobile Device'
            elif 'Windows' in user_agent:
                device_info = 'Windows PC'
            elif 'Mac' in user_agent:
                device_info = 'Mac Computer'
            elif 'Linux' in user_agent:
                device_info = 'Linux Computer'
            else:
                device_info = 'Web Browser'

            ip_address = self.get_client_ip(request)
            location = self.get_location_from_ip(ip_address)

            try:
                UserSession.objects.update_or_create(
                    user=user,
                    session_key=session_key,
                    defaults={
                        'device_info': device_info,
                        'ip_address': ip_address,
                        'location': location,
                        'user_agent': user_agent[:200],
                    }
                )
            except Exception:
                pass  # Игнорируем ошибки БД для сессий

    def get_client_ip(self, request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_location_from_ip(self, ip_address):
        """Получить примерное местоположение по IP (упрощенная версия)"""
        # В реальном приложении здесь был бы вызов геолокационного сервиса
        # Для демонстрации возвращаем фиктивные данные
        return "Москва, Россия"


class AuthDebugMiddleware:
    """Middleware для отладки аутентификации"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Логируем все запросы с заголовками
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_header:
            logger.info(f"🔍 AuthDebugMiddleware - Request: {request.method} {request.path}")
            logger.info(f"🔍 AuthDebugMiddleware - Auth header: {auth_header[:50]}..." if len(auth_header) > 50 else f"🔍 AuthDebugMiddleware - Auth header: {auth_header}")
            logger.info(f"🔍 AuthDebugMiddleware - User: {request.user if hasattr(request, 'user') else 'No user'}")

        response = self.get_response(request)

        return response