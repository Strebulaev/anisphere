"""
Permission classes for subscription checks
"""
from rest_framework.permissions import BasePermission


class IsPremiumUser(BasePermission):
    """
    Проверяет, имеет ли пользователь премиум-подписку.
    Для скачивания опенингов/эндингов и серий.
    """
    message = 'Для скачивания необходима подписка. Активировать подписку можно в настройках профиля.'

    def has_permission(self, request, view):
        # Анонимные пользователи не могут скачивать
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Проверяем подписку
        from users.models import Subscription
        try:
            sub = request.user.subscription
            return sub.is_premium
        except Subscription.DoesNotExist:
            return False


def check_user_premium(user):
    """Хелпер для проверки премиума"""
    if not user:
        return False
    if not hasattr(user, 'is_authenticated'):
        return False
    if not user.is_authenticated:
        return False
    try:
        sub = user.subscription
        if sub is None:
            return False
        return bool(getattr(sub, 'is_premium', False))
    except Exception:
        return False


def check_premium_or_403(user):
    """Проверяет подписку и возвращает False если нет"""
    return check_user_premium(user)
