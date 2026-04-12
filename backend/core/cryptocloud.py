"""
CryptoCloud payment service - приём платежей в криптовалюте
Не проверяет контент, пофиг на авторские права
"""
import requests
import hashlib
import jwt
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CryptoCloudService:
    """Сервис для работы с CryptoCloud"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'CRYPTOCLOUD_API_KEY', '')
        self.shop_id = getattr(settings, 'CRYPTOCLOUD_SHOP_ID', '')
        self.secret_key = getattr(settings, 'CRYPTOCLOUD_SECRET_KEY', '')
        self.api_host = 'https://api.cryptocloud.plus'
        
    def create_invoice(self, amount: float, order_id: str = None, description: str = '') -> dict:
        """
        Создание счёта на оплату
        amount: сумма в рублях (RUB)
        """
        if not self.api_key:
            logger.error('CryptoCloud API key not configured')
            return {'success': False, 'error': 'Payment service not configured'}
        
        url = f'{self.api_host}/v2/invoice/create'
        
        headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # CryptoCloud: amount - сумма, currency - валюта для конвертации
        data = {
            'shop_id': self.shop_id,
            'amount': amount,  # Сумма в RUB
            'currency': 'RUB',  # Валюта создания
            'order_id': order_id,
            'description': description[:100] if description else 'Premium Subscription',
            'add_fields': {
                'time_to_pay': {'hours': 24, 'minutes': 0}
            }
        }
        
        logger.info(f'CryptoCloud request: {data}')
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()
            logger.info(f'CryptoCloud create invoice response: {result}')
            
            if response.status_code == 200 and result.get('status') == 'success':
                result_data = result.get('result', {})
                return {
                    'success': True,
                    'invoice_id': result_data.get('uuid'),
                    'invoice_uuid': result_data.get('uuid'),
                    'payment_url': result_data.get('link') or result_data.get('pay_url'),
                    'amount': amount,
                    'amount_in_fiat': result_data.get('amount_in_fiat'),
                    'currency': 'RUB',
                }
            else:
                logger.error(f'CryptoCloud error: {result}')
                return {
                    'success': False,
                    'error': result.get('message', result.get('result', 'Payment creation failed'))
                }
        except Exception as e:
            logger.error(f'CryptoCloud exception: {e}')
            return {'success': False, 'error': str(e)}
    
    def check_payment(self, invoice_uuid: str) -> dict:
        """Проверка статуса платежа по UUID"""
        if not self.api_key:
            return {'success': False, 'error': 'Not configured'}
        
        url = f'{self.api_host}/v2/invoice/merchant/info'
        
        headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'uuids': [invoice_uuid]
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()
            
            if response.status_code == 200 and result.get('status') == 'success':
                invoices = result.get('result', [])
                if invoices:
                    invoice = invoices[0]
                    status_map = {
                        'created': 'pending',
                        'paid': 'paid',
                        'overpaid': 'paid',
                        'partial': 'pending',
                        'canceled': 'canceled'
                    }
                    return {
                        'success': True,
                        'status': status_map.get(invoice.get('status'), 'unknown'),
                        'amount': invoice.get('amount_usd'),
                        'amount_paid': invoice.get('amount_paid_usd'),
                        'currency': invoice.get('currency', {}).get('code'),
                    }
            return {'success': False, 'error': 'Invoice not found'}
        except Exception as e:
            logger.error(f'CryptoCloud check error: {e}')
            return {'success': False, 'error': str(e)}

    def verify_webhook_token(self, token: str) -> bool:
        """Проверка JWT токена из webhook"""
        if not self.secret_key or not token:
            return False
        try:
            jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True
        except jwt.PyJWTError as e:
            logger.warning(f'JWT verification failed: {e}')
            return False


# Глобальный экземпляр
cryptocloud_service = CryptoCloudService()
