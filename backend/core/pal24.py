"""
Pal24 (pally.info) payment service integration
"""
import hashlib
import requests
from django.conf import settings
from django.utils import timezone


class Pal24PaymentService:
    """Сервис для работы с Pal24 API"""
    
    BASE_URL = 'https://pal24.pro/api/v1'
    
    def __init__(self):
        self.api_token = getattr(settings, 'PAL24_API_TOKEN', None)
        self.shop_id = getattr(settings, 'PAL24_SHOP_ID', None)
    
    def _get_headers(self):
        """Заголовки для запросов"""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    
    def _generate_signature(self, *args):
        """Генерация подписи для postback"""
        data = ':'.join(str(arg) for arg in args)
        return hashlib.md5(data.encode()).hexdigest().upper()
    
    def verify_signature(self, out_sum, inv_id, signature):
        """Проверка подписи postback"""
        if not self.api_token:
            return False
        expected = self._generate_signature(out_sum, inv_id, self.api_token)
        return expected.upper() == signature.upper()
    
    def create_bill(self, amount, order_id, description='', custom=None):
        """
        Создание счета на оплату
        
        :param amount: Сумма в рублях
        :param order_id: Уникальный ID заказа (например, subscription-{user_id}-{timestamp})
        :param description: Описание платежа
        :param custom: Произвольные данные (например, user_id)
        :return: dict с link_url, link_page_url, bill_id
        """
        if not self.api_token or not self.shop_id:
            return {
                'success': False,
                'error': 'Pal24 API не настроен'
            }
        
        data = {
            'amount': str(amount),
            'shop_id': self.shop_id,
            'order_id': order_id,
            'description': description or 'Оплата подписки Anisphere',
            'type': 'normal',
            'currency_in': 'RUB',
            'payer_pays_commission': '1',  # Комиссию платит покупатель
            'name': 'Подписка Premium',
        }
        
        if custom:
            data['custom'] = str(custom)
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/bill/create',
                data=data,
                headers=self._get_headers(),
                timeout=30
            )
            result = response.json()
            
            if result.get('success') == 'true' or result.get('success') is True:
                return {
                    'success': True,
                    'link_url': result.get('link_url'),
                    'link_page_url': result.get('link_page_url'),
                    'bill_id': result.get('bill_id'),
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Ошибка создания счета')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_bill_status(self, bill_id):
        """Получение статуса счета"""
        if not self.api_token:
            return None
        
        try:
            response = requests.get(
                f'{self.BASE_URL}/bill/status',
                params={'id': bill_id},
                headers=self._get_headers(),
                timeout=30
            )
            result = response.json()
            if result.get('success'):
                return result
            return None
        except Exception:
            return None
    
    def get_payment_status(self, payment_id):
        """Получение статуса платежа"""
        if not self.api_token:
            return None
        
        try:
            response = requests.get(
                f'{self.BASE_URL}/payment/status',
                params={'id': payment_id},
                headers=self._get_headers(),
                timeout=30
            )
            result = response.json()
            if result.get('success'):
                return result
            return None
        except Exception:
            return None


# Глобальный экземпляр
pal24_service = Pal24PaymentService()
