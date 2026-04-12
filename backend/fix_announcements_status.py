#!/usr/bin/env python3
"""
Скрипт исправления статусов анонсов.
- Анонсы (announced) без эпизодов и без kodik_link остаются анонсами
- Если у аниме есть эпизоды и kodik_link - это не анонс, переводим в finished
- Если аниме в статусе finished/released но нет эпизодов и нет kodik_link - возвращаем в announced
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from django.utils import timezone

def fix_announcements():
    """Исправляет статусы анонсов."""
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ СТАТУСОВ АНОНСОВ")
    print("=" * 60)
    
    # 1. Находим анонсы (announced) которые уже вышли - переводим в finished
    # Критерии: есть episodes > 1 ИЛИ есть kodik_link
    announced_that_released = Anime.objects.filter(status='announced').filter(
        models.Q(episodes__gt=1) | models.Q(kodik_link__isnull=False, kodik_link__gt='')
    )
    
    count_announced_to_finished = announced_that_released.count()
    print(f"\n📊 Анонсы которые уже вышли (переводим в finished): {count_announced_to_finished}")
    
    if count_announced_to_finished > 0:
        for anime in announced_that_released[:20]:  # Показываем первые 20
            print(f"  [{anime.id}] {anime.title_ru[:40]} - episodes: {anime.episodes}, has_kodik: {bool(anime.kodik_link)}")
        
        confirm = input(f"\nПеревести {count_announced_to_finished} аниме в finished? (y/n): ").strip().lower()
        if confirm == 'y':
            updated = announced_that_released.update(status='finished', updated_at=timezone.now())
            print(f"  ✅ Обновлено: {updated}")
        else:
            print("  ❌ Отменено")
    
    # 2. Находим "фальшивые" finished/released - которые на самом деле анонсы
    # Критерии: status in (finished, released) И (нет episodes ИЛИ episodes = 0/1) И нет kodik_link
    fake_finished = Anime.objects.filter(
        models.Q(status='finished') | models.Q(status='released')
    ).filter(
        models.Q(episodes__isnull=True) | models.Q(episodes=0) | models.Q(episodes=1)
    ).filter(
        models.Q(kodik_link__isnull=True) | models.Q(kodik_link='')
    )
    
    count_fake_finished = fake_finished.count()
    print(f"\n📊 Фальшивые finished (возвращаем в announced): {count_fake_finished}")
    
    if count_fake_finished > 0:
        for anime in fake_finished[:20]:  # Показываем первые 20
            print(f"  [{anime.id}] {anime.title_ru[:40]} - episodes: {anime.episodes}")
        
        confirm = input(f"\nПеревести {count_fake_finished} аниме в announced? (y/n): ").strip().lower()
        if confirm == 'y':
            updated = fake_finished.update(status='announced', updated_at=timezone.now())
            print(f"  ✅ Обновлено: {updated}")
        else:
            print("  ❌ Отменено")
    
    # 3. Также проверим по году - если год в будущем, это анонс
    from datetime import date
    current_year = date.today().year
    
    future_released = Anime.objects.filter(
        models.Q(status='finished') | models.Q(status='released')
    ).filter(year__gt=current_year)
    
    count_future = future_released.count()
    print(f"\n📊 Finished с годом в будущем (> {current_year}): {count_future}")
    
    if count_future > 0:
        for anime in future_released[:20]:
            print(f"  [{anime.id}] {anime.title_ru[:40]} - year: {anime.year}")
        
        confirm = input(f"\nПеревести {count_future} аниме в announced? (y/n): ").strip().lower()
        if confirm == 'y':
            updated = future_released.update(status='announced', updated_at=timezone.now())
            print(f"  ✅ Обновлено: {updated}")
        else:
            print("  ❌ Отменено")
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    
    stats = {
        'announced': Anime.objects.filter(status='announced').count(),
        'ongoing': Anime.objects.filter(status='ongoing').count(),
        'finished': Anime.objects.filter(status='finished').count(),
        'released': Anime.objects.filter(status='released').count(),
        'canceled': Anime.objects.filter(status='canceled').count(),
    }
    
    print(f"  announced: {stats['announced']}")
    print(f"  ongoing:   {stats['ongoing']}")
    print(f"  finished:  {stats['finished']}")
    print(f"  released:  {stats['released']}")
    print(f"  canceled:  {stats['canceled']}")
    print(f"  ВСЕГО:     {sum(stats.values())}")


if __name__ == '__main__':
    # Добавляем импорт models
    from django.db import models
    fix_announcements()
