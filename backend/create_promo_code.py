#!/usr/bin/env python3
"""
Скрипт создания промокода ANI100 для пробной подписки на 15 дней (100% скидка)
"""

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from datetime import timedelta
from users.models import PromoCode

# Удаляем старый промокод если есть
PromoCode.objects.filter(code="ANI100").delete()

# Создаём новый промокод со 100% скидкой
promo = PromoCode.objects.create(
    code="ANI100",
    discount_percent=100,  # 100% скидка = бесплатно
    discount_amount=0,
    is_active=True,
    max_uses=3000,  # 3000 использований
    used_count=0,
    valid_until=timezone.now() + timedelta(days=31),  # Действителен 31 день
)

print(f"✅ Создан промокод: {promo.code}")
print(f"   Скидка: {promo.discount_percent}%")
print(f"   Действителен до: {promo.valid_until.strftime('%d.%m.%Y')}")
print(f"   Максимум использований: {promo.max_uses}")
print(
    f"\nПри активации подписка даст доступ к скачиванию опенингов/эндингов/фрагментов на 30 дней!"
)
