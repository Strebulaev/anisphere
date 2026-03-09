"""
Кастомный JWT-аутентификатор, который НЕ бросает 401
при невалидном/истёкшем токене для публичных эндпоинтов.

Стандартный JWTAuthentication при наличии Authorization-заголовка
с невалидным токеном выбрасывает AuthenticationFailed → 401,
даже если у вью стоит permission_classes = [AllowAny].

Этот класс при ошибке токена просто возвращает None (анонимный пользователь),
что позволяет AllowAny-вью работать нормально.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)


class SoftJWTAuthentication(JWTAuthentication):
    """
    JWT-аутентификация, которая не блокирует анонимный доступ
    при невалидном токене. Если токен невалиден — возвращает None
    вместо 401, позволяя permission_classes решить доступ.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed) as e:
            # Токен есть, но невалиден/истёк — не блокируем, возвращаем анонима
            # Permission-класс сам решит, нужна ли авторизация
            logger.debug(f"SoftJWTAuthentication: token invalid for {request.path}: {e}")
            return None
