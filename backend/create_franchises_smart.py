"""
Умная группировка аниме во франшизы.

Алгоритм:
1. Извлекает "ядро" названия (основу франшизы)
2. Группирует аниме по ядру
3. Создаёт франшизы в БД
4. Привязывает аниме к франшизам

Запуск: python backend/create_franchises_smart.py
"""

import os
import sys
import re
from collections import defaultdict
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime, Franchise
from django.db import transaction


# ============================================================================
# 1. НОРМАЛИЗАЦИЯ НАЗВАНИЙ
# ============================================================================

def normalize_title(title: str) -> str:
    """
    Базовая нормализация: lower case +.trim пробелов.
    """
    if not title:
        return ''
    return ' '.join(title.lower().split())


def clean_title_for_core(title: str) -> str:
    """
    Очищает название для извлечения ядра:
    - Убирает год в скобках: (2023), (2024)
    - Убирает тип в скобках: (TV), (TV-2), (OVA), (Movie), (ONA), (Special)
    - Убирает рейтинги: (16+), (18+)
    - Убирает OVA/ONA/Movie/3D/2D без скобок если в конце
    - Оставляет основное название с двоеточиями/тире
    """
    if not title:
        return ''
    
    # Убираем квадратные скобки [TV], [Dub] и т.д.
    title = re.sub(r'\s*\[[^\]]*\]\s*', ' ', title)
    
    # Убираем круглые скобки с годом, типом, рейтингом
    title = re.sub(r'\s*\(\s*(TV|TV-\d+|OVA|Movie|ONA|Special|OVA|ONA|Special|\d{4}|\d{4}-\d{4}|\d{2}[-+])\s*\)\s*', ' ', title, flags=re.IGNORECASE)
    
    # Убираем OVA/ONA/Movie/3D/2D в конце без скобок
    title = re.sub(r'\s+(OVA|ONA|Movie|Special|TV|3D|2D)\s*$', ' ', title, flags=re.IGNORECASE)
    
    # Убираем ". Фильм" в конце
    title = re.sub(r'\s*\.?\s*Фильм\s*$', ' ', title, flags=re.IGNORECASE)
    
    # Убираем лишние пробелы
    title = ' '.join(title.split())
    
    return title


# ============================================================================
# 2. ИЗВЛЕЧЕНИЕ ЯДРА ФРАНШИЗЫ
# ============================================================================

def extract_franchise_core(title: str) -> str:
    """
    Извлекает ядро франшизы из названия.
    
    Правила (по приоритету):
    1. Двоеточие или точка — берём всё до
    2. Тире с пробелами — берём всё до
    3. "на ..." (спецпроекты) — убираем
    4. "X. Часть Y" — убираем часть с цифрой
    5. "Сезон X", "Часть X", "ТВ-X" — убираем
    6. Год в скобках или просто год — убираем
    7. Цифра в конце — убираем
    8. Римская цифра — убираем
    9. Иначе очищенное название
    
    Возвращает нормализованное ядро (lower case).
    """
    if not title:
        return ''
    
    # Сначала чистим от годов и типов
    cleaned = clean_title_for_core(title)
    
    # 1. Двоеточие — основной разделитель
    if ':' in cleaned:
        core = cleaned.split(':')[0].strip()
        return normalize_title(core)
    
    # 1б. Точка как разделитель (но не в конце)
    # "Ван-Пис. Фильм" → "ван-пис"
    if '.' in cleaned and not cleaned.endswith('.'):
        core = cleaned.split('.')[0].strip()
        return normalize_title(core)
    
    # 2. Тире с пробелами
    match = re.search(r'\s+—\s+', cleaned)
    if match:
        core = cleaned[:match.start()].strip()
        if core:
            return normalize_title(core)
    
    # 3. "на ..." — спецпроекты (Ван-Пис на токийской...)
    match = re.search(r'\s+на\s+.+$', cleaned, re.IGNORECASE)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 4. "X. Часть Y"
    match = re.search(r'\s+\d+\.\s*Часть\s+\d+$', cleaned, re.IGNORECASE)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 5. "Часть X"
    match = re.search(r'\s+Часть\s+\d+$', cleaned, re.IGNORECASE)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 6. "Сезон X"
    match = re.search(r'\s+Сезон\s+\d+$', cleaned, re.IGNORECASE)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 7. "ТВ-X"
    match = re.search(r'\s+\(?(TV|ТВ)\s*-?\s*\d+\)?$', cleaned, re.IGNORECASE)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 8. Год в скобках в конце
    match = re.search(r'\s*\(\s*\d{4}\s*\)\s*$', cleaned)
    if match:
        core = cleaned[:match.start()].strip()
        return normalize_title(core)
    
    # 9. Просто год в конце
    match = re.search(r'\s+(\d{4})$', cleaned)
    if match:
        core = cleaned[:match.start()].strip()
        if core and len(core) > 3:
            return normalize_title(core)
    
    # 10. Цифра в конце
    match = re.match(r'(.+?)\s+(\d+)$', cleaned)
    if match:
        core = match.group(1).strip()
        return normalize_title(core)
    
    # 11. Римская цифра
    match = re.match(r'(.+?)\s+(II|III|IV|V|VI|VII|VIII|IX|X)$', cleaned, re.IGNORECASE)
    if match:
        core = match.group(1).strip()
        return normalize_title(core)
    
    # 12. Ничего не найдено
    return normalize_title(cleaned)


def get_franchise_priority_name(titles: list[str]) -> str:
    """
    Выбирает лучшее название для франшизы из списка названий аниме.
    
    Приоритет:
    1. Самое короткое название (обычно основное)
    2. Без подзаголовков (без двоеточия)
    3. С максимальным количеством слов
    """
    if not titles:
        return ''
    
    # Сортируем: сначала без двоеточий, потом по длине
    def score(title):
        has_colon = 1 if ':' in title else 0
        length = len(title)
        return (has_colon, length)
    
    sorted_titles = sorted(titles, key=score)
    return sorted_titles[0]


# ============================================================================
# 3. ГРУППИРОВКА
# ============================================================================

def group_anime_into_franchises():
    """
    Группирует все аниме в франшизы по ядру названия.
    
    Возвращает dict: {franchise_core: [anime_id, ...]}
    """
    print("📊 Группировка аниме по франшизам...")
    
    # Получаем все аниме с русскими названиями
    animes = Anime.objects.filter(title_ru__isnull=False).exclude(title_ru='').only('id', 'title_ru')
    
    core_groups = defaultdict(list)
    
    for anime in animes:
        core = extract_franchise_core(anime.title_ru)
        if core:
            core_groups[core].append(anime.id)
    
    print(f"  Найдено {len(core_groups)} потенциальных франшиз")
    
    # ФИЛЬТР: оставляем только франшизы с 2+ аниме
    multi_anime = {k: v for k, v in core_groups.items() if len(v) >= 2}
    filtered_count = len(core_groups) - len(multi_anime)
    
    print(f"  Франшиз с 2+ аниме: {len(multi_anime)}")
    print(f"  Отфильтровано одиночек: {filtered_count}")
    
    # Статистика
    sizes = defaultdict(int)
    for core, ids in multi_anime.items():
        sizes[len(ids)] += 1
    
    print("  Распределение по размеру:")
    for size in sorted(sizes.keys()):
        print(f"    {size} аниме: {sizes[size]} франшиз")
    
    return multi_anime


# ============================================================================
# 4. СОЗДАНИЕ ФРАНШИЗ В БД
# ============================================================================

@transaction.atomic
def create_franchises_from_groups(core_groups: dict[str, list[int]]):
    """
    Создаёт франшизы в БД и привязывает аниме.
    """
    print("\n📁 Создание франшиз в БД...")
    
    # Сбрасываем старые франшизы
    old_count = Franchise.objects.count()
    if old_count > 0:
        print(f"  ⚠️ Удаляем {old_count} старых франшиз...")
        Franchise.objects.all().delete()
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    for core, anime_ids in core_groups.items():
        try:
            # Получаем названия аниме для выбора имени франшизы
            titles = list(Anime.objects.filter(id__in=anime_ids)
                         .values_list('title_ru', flat=True))
            
            # Выбираем лучшее название для франшизы
            franchise_name = get_franchise_priority_name(titles)
            
            # Создаём или обновляем франшизу
            franchise, created = Franchise.objects.update_or_create(
                name=franchise_name,
                defaults={
                    'description': f'Франшиза "{franchise_name}"',
                }
            )
            
            # Привязываем аниме к франшизе
            Anime.objects.filter(id__in=anime_ids).update(franchise=franchise)
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            # Прогресс каждые 100
            if (created_count + updated_count) % 100 == 0:
                print(f"  Обработано {created_count + updated_count} франшиз...")
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Error creating franchise for core "{core}": {e}')
            error_count += 1
    
    print(f"\n✅ Франшизы созданы:")
    print(f"  Создано: {created_count}")
    print(f"  Обновлено: {updated_count}")
    print(f"  Ошибок: {error_count}")


# ============================================================================
# 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def print_franchise_examples(core_groups: dict[str, list[int]], limit: int = 20):
    """
    Показывает примеры сгруппированных франшиз.
    """
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ ФРАНШИЗ")
    print("=" * 60)
    
    # Сортируем по количеству аниме (убывание)
    sorted_cores = sorted(core_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    for core, anime_ids in sorted_cores[:limit]:
        titles = list(Anime.objects.filter(id__in=anime_ids)
                     .values_list('title_ru', flat=True)[:5])
        
        print(f"\n📁 {core.upper()} ({len(anime_ids)} аниме)")
        for t in titles:
            print(f"  - {t}")
        if len(anime_ids) > 5:
            print(f"  ... и ещё {len(anime_ids) - 5}")


def verify_franchises():
    """
    Проверяет результат группировки.
    """
    print("\n" + "=" * 60)
    print("ПРОВЕРКА РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    total_franchises = Franchise.objects.count()
    print(f"Всего франшиз: {total_franchises}")
    
    # Франшизы с количеством аниме (используем correct related_name='entries')
    from django.db.models import Count
    stats = Franchise.objects.annotate(anime_count=Count('entries')).order_by('-anime_count')[:20]
    
    print("\nТоп-20 франшиз по количеству аниме:")
    for f in stats:
        print(f"  {f.name}: {f.anime_count} аниме")
    
    # Аниме без франшизы
    no_franchise = Anime.objects.filter(franchise__isnull=True).count()
    print(f"\nАниме без франшизы: {no_franchise}")


# ============================================================================
# 6. MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("УМНАЯ ГРУППИРОВКА АНИМЕ ВО ФРАНШИЗЫ")
    print("=" * 60)
    print()
    
    # Шаг 1: Группировка
    core_groups = group_anime_into_franchises()
    
    # Шаг 2: Показываем примеры
    print_franchise_examples(core_groups)
    
    # Шаг 3: Спрашиваем подтверждение
    print("\n" + "=" * 60)
    print("СОЗДАТЬ ФРАНШИЗЫ В БД?")
    print("=" * 60)
    print("Это удалит все старые франшизы и создаст новые.")
    print()
    response = input("Продолжить? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Отменено")
        return
    
    # Шаг 4: Создаём франшизы
    create_franchises_from_groups(core_groups)
    
    # Шаг 5: Проверка
    verify_franchises()
    
    print("\n✅ Готово!")


if __name__ == '__main__':
    main()
