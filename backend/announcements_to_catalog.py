#!/usr/bin/env python3
"""
Скрипт перевода анонсов в каталог (finished).
Переводит анонсы у которых год выхода < 2026
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from django.db import models
from django.utils import timezone
from datetime import date

def announcements_to_catalog():
    """Переводит старые анонсы в каталог."""
    
    current_year = date.today().year
    
    print("=" * 60)
    print("ПЕРЕВОД АНОНСОВ В КАТАЛОГ")
    print("=" * 60)
    print(f"Текущий год: {current_year}")
    print(f"Переводим анонсы с годом < 2026")
    
    # Находим анонсы с годом до 2026
    old_announcements = Anime.objects.filter(status='announced').filter(
        models.Q(year__lt=2026)
    )
    
    count = old_announcements.count()
    print(f"\n📊 Найдено анонсов с годом < 2026: {count}")
    
    if count == 0:
        print("  Нет анонсов для перевода!")
        return
    
    # Показываем первые 30
    print("\nПервые 30 аниме:")
    for anime in old_announcements[:30]:
        print(f"  [{anime.id}] {anime.title_ru[:50]} (год: {anime.year})")
    
    if count > 30:
        print(f"  ... и ещё {count - 30}")
    
    # Подтверждение
    confirm = input(f"\nПеревести {count} аниме в finished? (y/n): ").strip().lower()
    
    if confirm == 'y':
        updated = old_announcements.update(status='finished', updated_at=timezone.now())
        print(f"\n✅ Готово! Обновлено: {updated}")
        
        # Показываем итоги
        print("\n" + "=" * 60)
        print("ИТОГИ")
        print("=" * 60)
        
        stats = {
            'announced': Anime.objects.filter(status='announced').count(),
            'ongoing': Anime.objects.filter(status='ongoing').count(),
            'finished': Anime.objects.filter(status='finished').count(),
            'released': Anime.objects.filter(status='released').count(),
        }
        
        print(f"  announced (анонсы): {stats['announced']}")
        print(f"  ongoing (онгоинг):  {stats['ongoing']}")
        print(f"  finished (вышедшие): {stats['finished']}")
        print(f"  released:           {stats['released']}")
    else:
        print("\n❌ Отменено")


if __name__ == '__main__':
    announcements_to_catalog()
