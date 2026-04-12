"""
Views для подписки и промокодов

============================================================================
КОММЕНТАРИЙ: ПОДПИСКА ОТКЛЮЧЕНА - ВЕСЬ ФУНКЦИОНАЛ БЕСПЛАТНЫЙ
============================================================================
Код сохранён для возможного использования в будущем.
Все эндпоинты возвращают is_premium=True для всех пользователей.
============================================================================
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone


class SubscriptionView(APIView):
    """Получение информации о подписке"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /users/subscription/ - получить информацию о подписке
        
        ИЗМЕНЕНО: Теперь всегда возвращает is_premium=True для всех
        """
        from users.models import Subscription
        from django.utils import timezone
        
        sub, created = Subscription.objects.get_or_create(user=request.user)
        
        # ====================================================================
        # ИЗМЕНЕНО: Весь функционал бесплатный - всегда True
        # ====================================================================
        is_premium = True  # Было: sub.is_premium
        
        # Считаем оставшиеся дни (всегда 999 - "бесконечно")
        days_left = 999
        
        return Response({
            'is_active': is_premium,
            'is_premium': is_premium,
            'started_at': sub.started_at.isoformat() if sub.started_at else None,
            'expires_at': sub.expires_at.isoformat() if sub.expires_at else None,
            'auto_renew': sub.auto_renew,
            'payment_method': sub.payment_method,
            'days_left': days_left,
            'note': 'Весь функционал бесплатный!',  # Добавленная заметка
        })


# ============================================================================
# КЛАСС SubscriptionActivateView ЗАКОММЕНТИРОВАН - ПОДПИСКА БЕСПЛАТНАЯ
# ============================================================================
# class SubscriptionActivateView(APIView):
#     """Активация подписки"""
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         """POST /users/subscription/activate/ - активировать подписку"""
#         from users.models import Subscription, PromoCode, PromoCodeUsage
#         
#         promo_code = request.data.get('promo_code', '').strip().upper()
#         days = request.data.get('days', 30)
#         
#         sub, created = Subscription.objects.get_or_create(user=request.user)
#         
#         discount = 0
#         if promo_code:
#             try:
#                 promo = PromoCode.objects.get(code=promo_code)
#                 if promo.is_valid():
#                     discount = promo.get_discount(399)
#                     promo.used_count += 1
#                     promo.save()
#                     PromoCodeUsage.objects.create(promo_code=promo, user=request.user)
#                 else:
#                     return Response({'error': 'Промокод недействителен или истек'}, status=400)
#             except PromoCode.DoesNotExist:
#                 return Response({'error': 'Промокод не найден'}, status=400)
#         
#         if isinstance(days, str):
#             days = int(days) if days.isdigit() else 30
#         
#         sub.activate(days=days, payment_method='promo' if promo_code else 'free')
#         sub.save()
#         
#         # Обновляем is_premium в профиле
#         try:
#             profile_settings = request.user.profile_settings
#             profile_settings.is_premium = True
#             profile_settings.save()
#         except Exception:
#             pass
#         
#         return Response({
#             'success': True,
#             'is_premium': True,
#             'started_at': sub.started_at.isoformat() if sub.started_at else None,
#             'expires_at': sub.expires_at.isoformat() if sub.expires_at else None,
#             'discount_applied': discount,
#             'message': f'Подписка активирована!{f" Скидка: {discount}₽" if discount else ""}'
#         })
# ============================================================================


# ============================================================================
# КЛАСС SubscriptionDeactivateView ЗАКОММЕНТИРОВАН - ПОДПИСКА БЕСПЛАТНАЯ
# ============================================================================
# class SubscriptionDeactivateView(APIView):
#     """Деактивация подписки"""
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         """POST /users/subscription/deactivate/ - деактивировать подписку"""
#         from users.models import Subscription
#         
#         try:
#             sub = Subscription.objects.get(user=request.user)
#             sub.deactivate()
#             
#             try:
#                 profile_settings = request.user.profile_settings
#                 profile_settings.is_premium = False
#                 profile_settings.save()
#             except Exception:
#                 pass
#             
#             return Response({'success': True, 'message': 'Подписка деактивирована'})
#         except Subscription.DoesNotExist:
#             return Response({'error': 'Подписка не найдена'}, status=404)
# ============================================================================


# ============================================================================
# КЛАСС PromoCodeValidateView ЗАКОММЕНТИРОВАН - ПОДПИСКА БЕСПЛАТНАЯ
# ============================================================================
# class PromoCodeValidateView(APIView):
#     """Валидация промокода"""
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         """GET /users/subscription/promo/validate/?code=XXX"""
#         from users.models import PromoCode
#         
#         code = request.query_params.get('code', '').strip().upper()
#         
#         if not code:
#             return Response({'valid': False, 'error': 'Код не указан'}, status=400)
#         
#         try:
#             promo = PromoCode.objects.get(code=code)
#             
#             if not promo.is_valid():
#                 return Response({'valid': False, 'error': 'Промокод недействителен или истек'})
#             
#             return Response({
#                 'valid': True,
#                 'discount_percent': promo.discount_percent,
#                 'discount_amount': promo.discount_amount,
#                 'discount': promo.get_discount(399),
#                 'price_after_discount': 399 - promo.get_discount(399),
#                 'message': f'Скидка {promo.discount_percent}% или {promo.discount_amount}₽'
#             })
#         except PromoCode.DoesNotExist:
#             return Response({'valid': False, 'error': 'Промокод не найден'})
# ============================================================================


# ============================================================================
# КЛАСС PromoCodeApplyView ЗАКОММЕНТИРОВАН - ПОДПИСКА БЕСПЛАТНАЯ
# ============================================================================
# class PromoCodeApplyView(APIView):
#     """Применение промокода"""
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         """POST /users/subscription/promo/apply/ - применить промокод"""
#         from users.models import PromoCode, PromoCodeUsage
#         
#         code = request.data.get('code', '').strip().upper()
#         
#         if not code:
#             return Response({'error': 'Код не указан'}, status=400)
#         
#         try:
#             promo = PromoCode.objects.get(code=code)
#             
#             if not promo.is_valid():
#                 return Response({'error': 'Промокод недействителен или истек'}, status=400)
#             
#             if PromoCodeUsage.objects.filter(promo_code=promo, user=request.user).exists():
#                 return Response({'error': 'Вы уже использовали этот промокод'}, status=400)
#             
#             promo.used_count += 1
#             promo.save()
#             PromoCodeUsage.objects.create(promo_code=promo, user=request.user)
#             
#             return Response({
#                 'success': True,
#                 'discount': promo.get_discount(399),
#                 'price_after_discount': 399 - promo.get_discount(399),
#                 'message': f'Промокод применен! Скидка {promo.get_discount(399)}₽'
#             })
#         except PromoCode.DoesNotExist:
#             return Response({'error': 'Промокод не найден'}, status=404)
# ============================================================================


# ============================================================================
# КЛАСС SubscriptionPriceView ЗАКОММЕНТИРОВАН - ПОДПИСКА БЕСПЛАТНАЯ
# ============================================================================
# class SubscriptionPriceView(APIView):
#     """Получение цены подписки"""
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         """GET /users/subscription/price/ - получить цену подписки"""
#         from users.models import PromoCode
#         
#         base_price = 399
#         promo_code = request.query_params.get('promo', '').strip().upper()
#         
#         discount = 0
#         if promo_code:
#             try:
#                 promo = PromoCode.objects.get(code=promo_code)
#                 if promo.is_valid():
#                     discount = promo.get_discount(base_price)
#             except PromoCode.DoesNotExist:
#                 pass
#         
#         return Response({
#             'base_price': base_price,
#             'discount': discount,
#             'final_price': base_price - discount,
#             'currency': 'RUB',
#             'period': 'month',
#             'features': [
#                 'Скачивание опенингов и эндингов',
#                 'Выбор формата MP3 или видео',
#                 'Корона в профиле',
#                 'Шапка профиля',
#                 'Соцсети в профиле',
#                 'Без рекламы',
#                 'Эксклюзивные значки'
#             ]
#         })
# ============================================================================
