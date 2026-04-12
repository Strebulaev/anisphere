"""
Проверка ошибок импорта из Kodik.

Запуск: python backend/check_import_errors.py
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime
from django.db.models import Count

KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'

# Проверяем аниме без shikimori_id
print("=" * 60)
print("ПРОВЕРКА ПРОБЛЕМНЫХ АНИМЕ")
print("=" * 60)

# 1. Аниме без shikimori_id
no_shiki = Anime.objects.filter(shikimori_id__isnull=True).count()
print(f"\n1. Аниме без Shikimori ID: {no_shiki}")

# 2. Аниме без названия
no_title = Anime.objects.filter(title_ru='', title_en='').count()
print(f"2. Аниме без названия: {no_title}")

# 3. Аниме с пустым poster_url
no_poster = Anime.objects.filter(poster_url='').count()
print(f"3. Аниме без постера: {no_poster}")

# 4. Аниме со статусом announced
announced = Anime.objects.filter(status='announced').count()
print(f"4. Анонсы (status='announced'): {announced}")

# 5. Общая статистика
print("\n" + "=" * 60)
print("ОБЩАЯ СТАТИСТИКА")
print("=" * 60)

total = Anime.objects.count()
print(f"Всего аниме: {total}")

stats = Anime.objects.values('status').annotate(count=Count('id'))
print("\nПо статусам:")
for s in stats:
    print(f"  {s['status']}: {s['count']}")

# 6. Примеры аниме без shikimori_id
print("\n" + "=" * 60)
print("ПРИМЕРЫ АНИМЕ БЕЗ SHIKIMORI ID (первые 10)")
print("=" * 60)
for anime in Anime.objects.filter(shikimori_id__isnull=True)[:10]:
    print(f"  ID={anime.id}: {anime.title_ru or anime.title_en} (kodik_id={anime.kodik_id})")
