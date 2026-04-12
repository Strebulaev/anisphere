#!/usr/bin/env python3
"""
Скрипт создания промокода ANI15 для пробной подписки на 15 дней (100% скидка)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from users.models import PromoCode

# Удаляем старый промокод если есть
PromoCode.objects.filter(code='ANI15').delete()

# Создаём новый промокод со 100% скидкой
promo = PromoCode.objects.create(
    code='ANI15',
    discount_percent=100,  # 100% скидка = бесплатно
    discount_amount=0,
    is_active=True,
    max_uses=999999,  # Безлимит
    used_count=0,
    valid_until=timezone.now() + timedelta(days=365),  # Действителен год
)

print(f"✅ Создан промокод: {promo.code}")
print(f"   Скидка: {promo.discount_percent}%")
print(f"   Действителен до: {promo.valid_until.strftime('%d.%m.%Y')}")
print(f"   Максимум использований: {promo.max_uses}")
print(f"\nПри активации подписка будет бесплатной!")
