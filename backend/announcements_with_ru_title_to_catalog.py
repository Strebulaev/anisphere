#!/usr/bin/env python3
"""
Скрипт перевода анонсов с русским названием в каталог (finished).
Переводит анонсы у которых есть title_ru на кириллице
"""

import os
import sys
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from django.db import models
from django.utils import timezone

def has_cyrillic(text):
    """Проверяет, есть ли кириллица в тексте"""
    if not text:
        return False
    # Ищем русские буквы (а-я, А-Я, включая ё)
    return bool(re.search(r'[а-яА-ЯёЁ]', text))

def announcements_with_ru_to_catalog():
    """Переводит анонсы с русским названием в каталог."""
    
    print("=" * 60)
    print("ПЕРЕВОД АНОНСОВ С РУССКИМ НАЗВАНИЕМ В КАТАЛОГ")
    print("=" * 60)
    
    # Находим все анонсы
    all_announced = Anime.objects.filter(status='announced')
    
    # Фильтруем только те, где title_ru содержит кириллицу
    announcements_with_ru = []
    for anime in all_announced:
        if anime.title_ru and has_cyrillic(anime.title_ru):
            announcements_with_ru.append(anime)
    
    count = len(announcements_with_ru)
    print(f"\n📊 Найдено анонсов с русским названием (кириллица): {count}")
    
    if count == 0:
        print("  Нет анонсов для перевода!")
        return
    
    # Показываем первые 30
    print("\nПервые 30 аниме:")
    for anime in announcements_with_ru[:30]:
        title = anime.title_ru[:50] if anime.title_ru else 'N/A'
        year = anime.year or 'N/A'
        print(f"  [{anime.id}] {title} (год: {year})")
    
    if count > 30:
        print(f"  ... и ещё {count - 30}")
    
    # Подтверждение
    confirm = input(f"\nПеревести {count} аниме в finished? (y/n): ").strip().lower()
    
    if confirm == 'y':
        ids = [a.id for a in announcements_with_ru]
        updated = Anime.objects.filter(id__in=ids).update(status='finished', updated_at=timezone.now())
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
    announcements_with_ru_to_catalog()
