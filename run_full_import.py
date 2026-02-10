#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный импорт аниме с очисткой БД
"""
import os
import sys
import django
import subprocess

# Найти все процессы Python и остановить их
# Get-Process python | Stop-Process -Force

# Или остановить конкретный процесс по имени скрипта
# Get-Process python | Where-Object {$_.Path -like "*python*"} | Stop-Process -Force

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime


def clear_anime_database():
    """Удаляет все аниме из БД"""
    print("\n" + "="*80)
    print("CLEARING ANIME DATABASE")
    print("="*80)
    
    total = Anime.objects.count()
    print(f"\nCurrent anime count: {total:,}")
    
    if total == 0:
        print("Database is already empty")
        return
    
    confirm = input(f"\nAre you sure you want to delete ALL {total:,} anime? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled")
        return
    
    Anime.objects.all().delete()
    print(f"Deleted {total:,} anime")
    
    remaining = Anime.objects.count()
    print(f"Remaining: {remaining:,}")
    
    if remaining == 0:
        print("Database cleared successfully")


def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("FULL ANIME IMPORT WITH IMAGES")
    print("="*80)
    
    clear_anime_database()
    
    print("\n" + "="*80)
    print("STARTING UNLIMITED IMPORT")
    print("="*80)
    print("\nRunning import_anime_with_bypass.py with:")
    print("  - Mode: UNLIMITED (all available anime)")
    print("  - Images: ENABLED")
    print("  - Fast mode: DISABLED (for reliability)")
    print("="*80 + "\n")
    
    cmd = [
        sys.executable,
        'import_anime_with_bypass.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nImport completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\nImport error: {e}")
        return False
    except KeyboardInterrupt:
        print("\nImport interrupted by user")
        return False
    
    print("\n" + "="*80)
    print("FINAL STATISTICS")
    print("="*80)
    
    total = Anime.objects.count()
    with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
    with_descriptions = Anime.objects.exclude(description__isnull=True).exclude(description='').count()
    with_titles_en = Anime.objects.exclude(title_en__isnull=True).exclude(title_en='').count()
    with_episodes = Anime.objects.exclude(episodes__isnull=True).count()
    
    print(f"\nOVERALL STATISTICS:")
    print(f"  Total anime: {total:,}")
    
    if total > 0:
        print(f"  With posters: {with_posters:,} ({with_posters/total*100:.1f}%)")
        print(f"  With descriptions: {with_descriptions:,} ({with_descriptions/total*100:.1f}%)")
        print(f"  With English titles: {with_titles_en:,} ({with_titles_en/total*100:.1f}%)")
        print(f"  With episode counts: {with_episodes:,} ({with_episodes/total*100:.1f}%)")
    else:
        print(f"  With posters: {with_posters:,}")
        print(f"  With descriptions: {with_descriptions:,}")
        print(f"  With English titles: {with_titles_en:,}")
        print(f"  With episode counts: {with_episodes:,}")
    
    print(f"\nEXAMPLES:")
    examples = Anime.objects.all()[:10]
    for i, anime in enumerate(examples, 1):
        poster = "[X]" if anime.poster else "[ ]"
        desc_preview = anime.description[:50] + "..." if anime.description and len(anime.description) > 50 else anime.description or "No description"
        print(f"  {i:2d}. {poster} {anime.title_ru[:40]:40}")
        if anime.title_en:
            print(f"      EN: {anime.title_en[:40]}")
        print(f"      Description: {desc_preview}")
        print(f"      Episodes: {anime.episodes or 'N/A'}, Year: {anime.year or 'N/A'}")
        print()
    
    print("="*80)
    print("DONE!")
    print("="*80)
    
    return True


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
