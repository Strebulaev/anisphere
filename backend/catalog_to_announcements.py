#!/usr/bin/env python3
"""
Скрипт переноса аниме с английским названием из каталога в анонсы.
Переводит аниме (finished/released) с title_en в статус announced.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from django.db import models
from django.utils import timezone

def catalog_to_announcements():
    """Переводит аниме с английским названием в анонсы."""
    
    print("=" * 60)
    print("ПЕРЕНОС ИЗ КАТАЛОГА В АНОНСЫ")
    print("=" * 60)
    
    # Находим finished/released с английским названием
    anime_with_en = Anime.objects.filter(
        models.Q(status='finished') | models.Q(status='released')
    ).filter(
        models.Q(title_en__isnull=False) & ~models.Q(title_en='')
    )
    
    count = anime_with_en.count()
    print(f"\n📊 Найдено аниме с title_en в каталоге: {count}")
    
    if count == 0:
        print("  Нет аниме для перевода!")
        return
    
    # Показываем первые 30
    print("\nПервые 30 аниме:")
    for anime in anime_with_en[:30]:
        title = anime.title_en[:50] if anime.title_en else 'N/A'
        status = anime.status
        year = anime.year or 'N/A'
        print(f"  [{anime.id}] {title}")
        print(f"      status: {status}, year: {year}")
    
    if count > 30:
        print(f"  ... и ещё {count - 30}")
    
    # Подтверждение
    confirm = input(f"\nПеревести {count} аниме в announced? (y/n): ").strip().lower()
    
    if confirm == 'y':
        updated = anime_with_en.update(status='announced', updated_at=timezone.now())
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
    catalog_to_announcements()
