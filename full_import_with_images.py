#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный импорт аниме с очисткой БД и скачиванием картинок
"""
import os
import sys
import django

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

def clear_anime_database():
    """Удаляет все аниме из БД"""
    print("\n" + "="*80)
    print("ОЧИСТКА БАЗЫ ДАННЫХ АНИМЕ")
    print("="*80)
    
    total = Anime.objects.count()
    print(f"\nТекущее количество аниме: {total:,}")
    
    if total == 0:
        print("База данных уже пуста")
        return
    
    confirm = input(f"\nВы уверены, что хотите удалить ВСЕ {total:,} аниме? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Операция отменена")
        return
    
    # Удаляем все аниме
    Anime.objects.all().delete()
    print(f"Удалено {total:,} аниме")
    
    # Проверяем
    remaining = Anime.objects.count()
    print(f"Осталось аниме: {remaining:,}")
    
    if remaining == 0:
        print("База данных полностью очищена")
    else:
        print(f"В базе осталось {remaining:,} аниме")

def clean_description(text):
    """Очищает описание от форматирования"""
    if not text:
        return ""
    
    # Удаляем HTML теги
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаляем специальные символы форматирования
    text = text.replace('\\n', ' ').replace('\\r', ' ')
    text = text.replace('\\b', '').replace('\\t', ' ')
    
    # Заменяем множественные пробелы на один
    text = re.sub(r'\s+', ' ', text)
    
    # Обрезаем
    text = text.strip()
    
    return text

def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("ПОЛНЫЙ ИМПОРТ АНИМЕ С КАРТИНКАМИ")
    print("="*80)
    
    # Шаг 1: Очистка БД
    clear_anime_database()
    
    # Шаг 2: Запуск импорта с картинками
    print("\n" + "="*80)
    print("ЗАПУСК ИМПОРТА АНИМЕ")
    print("="*80)
    print("\nЗапускаем import_anime_verbose.py с параметрами:")
    print("  - Максимальное количество: 100000")
    print("  - Скачивание картинок: ВКЛЮЧЕНО")
    print("  - Быстрый режим: ВЫКЛЮЧЕН (для надёжности)")
    print("="*80 + "\n")
    
    # Запускаем импорт через subprocess
    import subprocess
    
    cmd = [
        sys.executable,
        'import_anime_verbose.py',
        '--max', '100000'
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nИмпорт завершён успешно!")
    except subprocess.CalledProcessError as e:
        print(f"\nОшибка при импорте: {e}")
        return False
    except KeyboardInterrupt:
        print("\nИмпорт прерван пользователем")
        return False
    
    # Шаг 3: Статистика после импорта
    print("\n" + "="*80)
    print("СТАТИСТИКА ПОСЛЕ ИМПОРТА")
    print("="*80)
    
    total = Anime.objects.count()
    with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
    with_descriptions = Anime.objects.exclude(description__isnull=True).exclude(description='').count()
    with_titles_en = Anime.objects.exclude(title_en__isnull=True).exclude(title_en='').count()
    with_episodes = Anime.objects.exclude(episodes__isnull=True).count()
    
    print(f"\nОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего аниме: {total:,}")
    
    if total > 0:
        print(f"  С постерами: {with_posters:,} ({with_posters/total*100:.1f}%)")
        print(f"  С описаниями: {with_descriptions:,} ({with_descriptions/total*100:.1f}%)")
        print(f"  С англ. названиями: {with_titles_en:,} ({with_titles_en/total*100:.1f}%)")
        print(f"  С количеством серий: {with_episodes:,} ({with_episodes/total*100:.1f}%)")
    else:
        print(f"  С постерами: {with_posters:,}")
        print(f"  С описаниями: {with_descriptions:,}")
        print(f"  С англ. названиями: {with_titles_en:,}")
        print(f"  С количеством серий: {with_episodes:,}")
    
    # Примеры аниме
    print(f"\nПРИМЕРЫ АНИМЕ:")
    examples = Anime.objects.all()[:10]
    for i, anime in enumerate(examples, 1):
        poster = "✓" if anime.poster else "✗"
        desc_preview = anime.description[:50] + "..." if anime.description and len(anime.description) > 50 else anime.description or "Нет описания"
        print(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40}")
        if anime.title_en:
            print(f"      EN: {anime.title_en[:40]}")
        print(f"      Описание: {desc_preview}")
        print(f"      Серий: {anime.episodes or 'N/A'}, Год: {anime.year or 'N/A'}")
        print()
    
    print("="*80)
    print("ГОТОВО!")
    print("="*80)
    
    return True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОперация прервана пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
