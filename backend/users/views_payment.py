"""
Views для оплаты подписки через CryptoCloud (криптовалюта)
"""
import uuid
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription, PromoCode, PromoCodeUsage
from core.cryptocloud import cryptocloud_service

logger = logging.getLogger(__name__)


class CreatePaymentView(APIView):
    """Создание платежа на оплату подписки через CryptoCloud"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Проверяем, есть ли уже активная подписка
        try:
            existing_sub = user.subscription
            if existing_sub.is_premium:
                return Response({
                    'error': 'У вас уже есть активная подписка'
                }, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass
        
        # Получаем цену
        base_price = getattr(settings, 'SUBSCRIPTION_PRICE', 399)
        
        # Проверяем промокод
        promo_code = request.data.get('promo_code', '').strip().upper()
        final_price = base_price
        
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code, is_active=True)
                if promo.is_valid():
                    discount = promo.get_discount(base_price)
                    final_price = max(0, base_price - discount)
                else:
                    return Response({
                        'error': 'Промокод недействителен или истек'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except PromoCode.DoesNotExist:
                return Response({
                    'error': 'Промокод не найден'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем уникальный ID заказа
        order_id = f'sub-{user.id}-{uuid.uuid4().hex[:8]}'
        
        # CryptoCloud принимает сумму в валюте, указанной в currency
        # Если currency=RUB, то amount должен быть в рублях
        amount_rub = float(final_price)
        
        logger.info(f'Creating CryptoCloud invoice: amount={amount_rub} RUB, order_id={order_id}')
        
        result = cryptocloud_service.create_invoice(
            amount=amount_rub,
            order_id=order_id,
            description=f'Подписка Premium Anisphere на 30 дней'
        )
        
        if not result.get('success'):
            logger.error(f'CryptoCloud invoice creation failed: {result.get("error")}')
            return Response({
                'error': f'Не удалось создать платеж: {result.get("error", "Попробуйте позже")}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'success': True,
            'payment_url': result.get('payment_url'),
            'invoice_id': result.get('invoice_id'),
            'invoice_uuid': result.get('invoice_uuid'),
            'order_id': order_id,
            'amount': result.get('amount'),
            'amount_in_fiat': result.get('amount_in_fiat'),
            'currency': 'RUB (криптовалюта)',
            'payment_method': 'cryptocloud'
        })


class PaymentSuccessView(APIView):
    """Обработка успешного редиректа после оплаты"""
    permission_classes = [AllowAny]

    def get(self, request):
        """GET редирект - для простого редиректа на страницу подписки"""
        from django.shortcuts import redirect
        return redirect('/subscription?success=1')


class PaymentFailView(APIView):
    """Обработка неуспешного редиректа после оплаты"""
    permission_classes = [AllowAny]

    def get(self, request):
        """GET редирект - для простого редиректа на страницу подписки"""
        from django.shortcuts import redirect
        return redirect('/subscription?failed=1')


class PaymentWebhookView(APIView):
    """Обработка webhook от CryptoCloud"""
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Обработка webhook от CryptoCloud
        При успешной оплате - активируем подписку
        """
        data = request.data
        
        logger.info(f'CryptoCloud webhook received: {data}')
        
        # Получаем данные из webhook
        status = data.get('status')
        invoice_id = data.get('invoice_id')  # Без префикса INV-
        order_id = data.get('order_id')  # Наш order_id
        amount_crypto = data.get('amount_crypto')
        currency = data.get('currency')
        token = data.get('token')
        
        # Проверяем токен если настроен secret_key
        if not cryptocloud_service.verify_webhook_token(token):
            # Если нет secret_key - пропускаем проверку (для тестов)
            if not getattr(settings, 'CRYPTOCLOUD_SECRET_KEY', ''):
                logger.warning('CryptoCloud webhook: no secret key configured, skipping verification')
            else:
                logger.warning(f'CryptoCloud webhook: invalid token')
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Парсим user_id из order_id (формат: sub-{user_id}-{uuid})
        user_id = None
        if order_id:
            parts = order_id.split('-')
            if len(parts) >= 2:
                user_id = parts[1]
        
        if not user_id:
            logger.error(f'No user_id in webhook: order_id={order_id}')
            return Response({'error': 'No user_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f'User {user_id} not found for webhook')
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Обрабатываем статус платежа
        if status == 'success':
            # Активируем подписку
            sub, created = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'is_active': True,
                    'payment_method': 'cryptocloud',
                }
            )
            
            if not created:
                sub.is_active = True
                sub.payment_method = 'cryptocloud'
            
            sub.activate(days=30, payment_method='cryptocloud')
            
            # Обновляем is_premium
            try:
                profile_settings = user.profile_settings
                profile_settings.is_premium = True
                profile_settings.save()
            except Exception:
                pass
            
            logger.info(f'Subscription activated via webhook for user {user.id}, invoice {invoice_id}')
            return Response({'success': True})
        
        elif status in ('failed', 'canceled'):
            logger.info(f'Payment {status} for user {user.id}, invoice {invoice_id}')
            return Response({'success': True})
        
        return Response({'success': True})


class CheckPaymentView(APIView):
    """Проверка статуса платежа"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invoice_uuid = request.data.get('invoice_uuid')
        
        if not invoice_uuid:
            return Response({'error': 'invoice_uuid required'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = cryptocloud_service.check_payment(invoice_uuid)
        
        if result.get('success'):
            # Если оплачен - активируем подписку
            if result.get('status') == 'paid':
                user = request.user
                sub, created = Subscription.objects.get_or_create(
                    user=user,
                    defaults={
                        'is_active': True,
                        'payment_method': 'cryptocloud',
                    }
                )
                
                if not created:
                    sub.is_active = True
                    sub.payment_method = 'cryptocloud'
                
                sub.activate(days=30, payment_method='cryptocloud')
                
                try:
                    profile_settings = user.profile_settings
                    profile_settings.is_premium = True
                    profile_settings.save()
                except Exception:
                    pass
                
                return Response({
                    'success': True,
                    'status': 'paid',
                    'subscription_activated': True
                })
            
            return Response({
                'success': True,
                'status': result.get('status')
            })
        
        return Response({
            'success': False,
            'error': result.get('error', 'Check failed')
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_price(request):
    """Получение актуальной цены подписки"""
    base_price = getattr(settings, 'SUBSCRIPTION_PRICE', 399)
    
    # Проверяем промокод
    promo_code = request.query_params.get('promo', '').strip().upper()
    final_price = base_price
    discount = 0
    
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code, is_active=True)
            if promo.is_valid():
                discount = promo.get_discount(base_price)
                final_price = max(0, base_price - discount)
        except PromoCode.DoesNotExist:
            pass
    
    return Response({
        'base_price': base_price,
        'final_price': final_price,
        'discount': discount,
        'currency': 'RUB',
    })
