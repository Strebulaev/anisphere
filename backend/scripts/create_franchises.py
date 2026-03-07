#!/usr/bin/env python3
"""
Скрипт группировки аниме во франшизы.

Запуск из корня проекта (рядом с manage.py):
    source venv/bin/activate
    python scripts/create_franchises.py [--reset]

--reset  : сначала очистить все существующие франшизы и начать заново
"""

import os, sys, re, django, argparse
from collections import defaultdict
from difflib import SequenceMatcher

# ── Настройка окружения Django ────────────────────────────────
def find_project_root():
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(path, 'manage.py')):
            return path
        path = os.path.dirname(path)
    return None

project_root = find_project_root()
if not project_root:
    print("❌ Не найден manage.py. Запустите скрипт из папки проекта.")
    sys.exit(1)

print(f"📁 Корень проекта: {project_root}")
sys.path.insert(0, project_root)

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    for module in ('config.settings', 'backend.settings', 'core.settings', 'settings'):
        try:
            import importlib
            importlib.import_module(module)
            os.environ['DJANGO_SETTINGS_MODULE'] = module
            print(f"⚙️  Используем settings: {module}")
            break
        except ModuleNotFoundError:
            continue

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    print("❌ Не удалось определить DJANGO_SETTINGS_MODULE.")
    sys.exit(1)

django.setup()

from anime.models import Anime, Franchise
from django.utils.text import slugify

# ── ПАТТЕРНЫ ДЛЯ УДАЛЕНИЯ СУФФИКСОВ ──────────────────────────

# Полные паттерны для удаления (то, что ТОЧНО надо отрезать)
_SUFFIX_PATTERNS = [
    # Скобочные суффиксы всех видов: [ТВ-1], (TV-2), [ТВ, часть 1], (ТВ-4, часть 1)
    r'\s*[\[（(]\s*(?:тв|tv|сезон|season|часть|part)\s*[-–—]?\s*\d+\s*(?:[,，]\s*(?:часть|part)\s*\d+)?\s*[\]）)]\s*$',
    r'\s*[\[（(]\s*\d+\s*[-–—]?\s*(?:сезон|season|часть|part)\s*\d*\s*[\]）)]\s*$',
    
    # Форматы с запятой: ТВ-4, часть 1
    r'\s*[,，]\s*(?:часть|part)\s*\d+\s*$',
    
    # Чёткие обозначения сезона/части без скобок
    r'\s*[-–—]?\s*(?:сезон|season)\s*\d+\s*[-–—]?\s*(?:часть|part)\s*\d+\s*$',
    r'\s*[-–—]?\s*(?:тв|tv)\s*[-–—]?\s*\d+\s*[,，]?\s*(?:часть|part)\s*\d+\s*$',
    r'\s*[-–—]?\s*[ТТ][ВВ]\s*[-–—]?\s*\d+\s*[,，]?\s*(?:часть|part)\s*\d+\s*$',
    
    # Простые сезоны
    r'\s*[-–—]?\s*\d+[-й]?\s*(?:сезон|season)\s*$',
    r'\s*[-–—]?\s*(?:сезон|season)\s*\d+\s*$',
    
    # Простые части
    r'\s*[-–—]?\s*\d+[-я]?\s*(?:часть|part)\s*$',
    r'\s*[-–—]?\s*(?:часть|part)\s*\d+\s*$',
    
    # ТВ/ТВ-4 форматы
    r'\s*[-–—]?\s*[ТТ][ВВ]\s*[-–—]?\s*\d+\s*$',
    r'\s*[-–—]?\s*tv\s*[-–—]?\s*\d+\s*$',
    
    # Римские цифры
    r'\s+[IVX]+(?:-й)?\s*$',
    
    # Типы
    r'\s*[-–—:]?\s*(?:ova|ona|special|спецвыпуск|фильм|movie|film|полнометражный|полный метр)\s*$',
    r'\s*[-–—:]?\s*\(\s*(?:ova|ona|special|movie|film)\s*\)\s*$',
    
    # Годы в скобках в конце
    r'\s*[\[（(]\s*[12][0-9]{3}\s*[\]）)]\s*$',
]

# Слова, которые могут быть частью основного названия (не отрезаем)
_PROTECTED_WORDS = [
    'начало', 'продолжение', 'финал', 'конец', 'пролог', 'эпилог',
    'the beginning', 'the end', 'the final', 'the movie', 'the film',
    'первый', 'второй', 'третий', 'четвертый', 'пятый',
    'first', 'second', 'third', 'fourth', 'fifth',
    'last', 'final', 'movie', 'film', 'фильм',
    'хроники', 'chronicles', 'история', 'story', 'tale',
    'легенда', 'legend', 'миф', 'myth', 'сага', 'saga',
]

# Подзаголовки, которые могут быть отдельными частями
_SUBTITLE_PARTS = [
    'начало', 'продолжение', 'финал', 'конец',
    'the beginning', 'the end', 'the final',
    'первая глава', 'вторая глава', 'последняя глава',
    'first chapter', 'second chapter', 'last chapter',
]

# ── ОСНОВНЫЕ ФУНКЦИИ ─────────────────────────────────────────

def is_year(text):
    """Проверяет, является ли строка годом"""
    return bool(re.match(r'^[12][0-9]{3}$', text.strip()))


def normalize_title(title: str) -> str:
    """
    Полная нормализация названия для поиска похожих.
    Убирает все суффиксы, приводит к нижнему регистру.
    """
    if not title:
        return ""
    
    t = title.strip()
    original = t
    
    # Убираем год в скобках в конце
    t = re.sub(r'\s*[\[（(]\s*[12][0-9]{3}\s*[\]）)]\s*$', '', t)
    
    # Убираем все суффиксы
    prev = None
    while prev != t:
        prev = t
        for pat in _SUFFIX_PATTERNS:
            t = re.sub(pat, '', t, flags=re.IGNORECASE).strip()
        t = t.rstrip(':-–— ,.').strip()
    
    # Если после очистки осталось слишком короткое слово, возвращаем оригинал
    if len(t) < 3:
        return original
    
    return t.lower()


def extract_base_name(title: str) -> str:
    """
    Извлекает базовое название для группировки.
    Для сложных случаев типа "Атака титанов [ТВ-4, часть 1]" -> "Атака титанов"
    """
    if not title:
        return ""
    
    t = title.strip()
    
    # Сначала пробуем убрать квадратные скобки полностью
    bracket_match = re.search(r'^(.+?)\s*[\[（(].+[\]）)]\s*$', t)
    if bracket_match:
        base = bracket_match.group(1).strip()
        if len(base) >= 3:
            return base
    
    # Пробуем убрать после двоеточия, если подзаголовок не защищён
    if ':' in t or '：' in t:
        parts = re.split(r'[:：]', t, maxsplit=1)
        main_part = parts[0].strip()
        sub_part = parts[1].strip() if len(parts) > 1 else ""
        
        # Проверяем, является ли подзаголовок отдельной частью
        sub_lower = sub_part.lower()
        for protected in _SUBTITLE_PARTS:
            if protected in sub_lower:
                return t  # это отдельная часть, не группируем
        
        # Если подзаголовок короткий и не похож на отдельную часть
        if len(sub_part) < 30 and not is_year(sub_part):
            # Проверяем, не содержит ли он ключевых слов
            for word in _PROTECTED_WORDS:
                if word in sub_lower:
                    return t  # защищённое слово, оставляем
            
            # Иначе возвращаем основную часть
            if len(main_part) >= 3:
                return main_part
    
    # Применяем все паттерны удаления
    t_norm = normalize_title(t)
    
    # Если нормализованное название слишком короткое, возвращаем оригинал
    if len(t_norm) < 3:
        return t
    
    return t_norm


def similarity_ratio(a: str, b: str) -> float:
    """Сравнивает две строки на похожесть"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def should_group_together(title1: str, title2: str) -> bool:
    """
    Определяет, должны ли два аниме быть в одной группе.
    """
    if not title1 or not title2:
        return False
    
    t1_lower = title1.lower()
    t2_lower = title2.lower()
    
    # Точное совпадение после нормализации
    base1 = normalize_title(title1)
    base2 = normalize_title(title2)
    
    if base1 == base2 and len(base1) >= 3:
        return True
    
    # Одно содержит другое (длинное содержит короткое)
    if len(t1_lower) >= 5 and len(t2_lower) >= 5:
        if t1_lower in t2_lower or t2_lower in t1_lower:
            # Проверяем, не является ли это случайным совпадением
            ratio = similarity_ratio(t1_lower, t2_lower)
            if ratio > 0.8:
                return True
    
    # Похожесть строк
    if similarity_ratio(t1_lower, t2_lower) > 0.85:
        return True
    
    return False


def best_display_name(entries: list, base: str) -> str:
    """
    Восстанавливает красивое отображаемое название франшизы.
    """
    # Сортируем по длине оригинального названия
    candidates = sorted(entries, key=lambda a: len(a.title_ru or a.title_en or ''))
    
    for a in candidates:
        orig = a.title_ru or a.title_en or ''
        if not orig or len(orig) > 100:
            continue
        
        # Очищаем от скобок и суффиксов для отображения
        clean = re.sub(r'\s*[\[（(].*[\]）)]\s*$', '', orig).strip()
        clean = re.sub(r'\s*[-–—]\s*(?:сезон|season|часть|part)\s*\d+\s*$', '', clean, flags=re.IGNORECASE).strip()
        
        if len(clean) >= 3:
            # Если очищенное похоже на базу
            if similarity_ratio(clean.lower(), base.lower()) > 0.8:
                return clean
    
    # Если ничего не нашли, возвращаем базу с заглавной буквы
    return base.title()


def order_for(anime) -> int:
    """Определяет порядок сортировки внутри франшизы"""
    # Пытаемся извлечь номер из названия
    title = anime.title_ru or anime.title_en or ''
    
    # Поиск номера сезона/части
    season_match = re.search(r'(?:сезон|season|часть|part)\s*(\d+)', title, re.IGNORECASE)
    if season_match:
        season_num = int(season_match.group(1))
        return (anime.year or 9999) * 100000 + season_num * 1000 + anime.id
    
    # Поиск ТВ-номера
    tv_match = re.search(r'(?:тв|tv)\s*[-–—]?\s*(\d+)', title, re.IGNORECASE)
    if tv_match:
        tv_num = int(tv_match.group(1))
        return (anime.year or 9999) * 100000 + tv_num * 1000 + anime.id
    
    # По умолчанию сортируем по году и id
    return (anime.year or 9999) * 100000 + anime.id


def group_all_anime():
    """Группирует ВСЕ аниме с учётом всех возможных форматов названий"""
    all_anime = list(Anime.objects.all())
    print(f"\nВсего аниме в БД: {len(all_anime)}")

    # Сначала группируем по нормализованному названию
    groups = defaultdict(list)
    
    for a in all_anime:
        orig = a.title_ru or a.title_en or ''
        if not orig:
            continue
            
        base = extract_base_name(orig)
        if base:
            groups[base].append(a)
    
    # Дополнительно проверяем на похожесть между группами
    # (на случай, если одно и то же аниме записано по-разному)
    final_groups = defaultdict(list)
    processed = set()
    
    for base1, items1 in groups.items():
        if base1 in processed:
            continue
        
        # Начинаем новую группу
        current_group = items1.copy()
        processed.add(base1)
        
        # Ищем похожие группы
        for base2, items2 in groups.items():
            if base2 in processed or base2 == base1:
                continue
            
            # Проверяем похожесть базовых названий
            if similarity_ratio(base1, base2) > 0.8:
                current_group.extend(items2)
                processed.add(base2)
        
        # Сохраняем итоговую группу
        final_groups[base1] = current_group
    
    # Фильтруем только группы с 2+ элементами
    multi = {k: v for k, v in final_groups.items() if len(v) >= 2}
    
    print(f"Групп с 2+ аниме: {len(multi)}")
    
    # Покажем примеры для отладки
    if multi:
        print("\nПримеры групп:")
        for name, items in list(multi.items())[:10]:
            print(f"\n  📌 «{name}» ({len(items)} аниме):")
            for a in items[:5]:
                title = a.title_ru or a.title_en or '?'
                year = f"({a.year})" if a.year else ""
                kind = a.kind if hasattr(a, 'kind') else ''
                print(f"    - {title} {year} [{kind}]".strip())
            if len(items) > 5:
                print(f"      ... и ещё {len(items)-5}")
    
    return multi


def create_or_update_franchise(base_name: str, entries: list) -> Franchise:
    """Создаёт или обновляет франшизу для группы аниме"""
    # Выбираем лучшее аниме для извлечения данных
    best = max(entries, key=lambda a: (a.score or 0, a.year or 0, a.id))
    
    franchise_name = best_display_name(entries, base_name)

    # Постер
    poster_url = ''
    if best.poster:
        try:
            poster_url = best.poster.url
        except Exception:
            pass
    if not poster_url:
        poster_url = best.poster_url or ''

    # Рейтинг
    scores = [a.score for a in entries if a.score]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    
    # Годы
    years = sorted([a.year for a in entries if a.year])
    year_start = years[0] if years else None
    year_end = years[-1] if years else None

    # Описание
    description = best.description or ''
    if len(description) > 5000:
        description = description[:5000] + '...'

    # Создаём slug
    slug_base = slugify(franchise_name) or slugify(base_name) or f'franchise-{abs(hash(base_name)) % 99999}'
    slug = slug_base

    # Ищем существующую франшизу
    existing = Franchise.objects.filter(slug=slug).first()
    if existing:
        franchise = existing
        franchise.name = franchise_name
        franchise.score = avg_score
        franchise.year_start = year_start
        franchise.year_end = year_end
        franchise.description = description
        if poster_url:
            franchise.poster_url = poster_url
        franchise.save()
        print(f"  📝 Обновлена франшиза: {franchise.name}")
    else:
        # Уникализируем слаг
        counter = 1
        while Franchise.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1
            
        franchise = Franchise.objects.create(
            name=franchise_name,
            slug=slug,
            description=description,
            poster_url=poster_url,
            score=avg_score,
            year_start=year_start,
            year_end=year_end,
        )
        print(f"  ✨ Создана франшиза: {franchise.name}")

    # Сортируем и привязываем аниме
    sorted_entries = sorted(entries, key=order_for)
    for idx, anime in enumerate(sorted_entries, start=1):
        anime.franchise = franchise
        anime.franchise_order = idx
        anime.save(update_fields=['franchise', 'franchise_order'])

    return franchise


def reset_franchises():
    """Сбрасывает все привязки и удаляет существующие франшизы."""
    print("🗑️  Сброс всех франшиз...")
    count = Anime.objects.filter(franchise__isnull=False).update(franchise=None, franchise_order=0)
    print(f"   Отвязано {count} аниме")
    deleted, _ = Franchise.objects.all().delete()
    print(f"   Удалено {deleted} франшиз")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true', help='Сначала удалить все существующие франшизы')
    parser.add_argument('--yes', action='store_true', help='Не спрашивать подтверждения')
    args = parser.parse_args()

    print("=" * 60)
    print("  Создание франшиз из аниме с похожими названиями")
    print("=" * 60)

    if args.reset:
        reset_franchises()

    groups = group_all_anime()

    if not groups:
        print("\nНет групп для объединения.")
        return

    total_anime_to_group = sum(len(v) for v in groups.values())
    print(f"\n📊 Итого:")
    print(f"   Франшиз будет создано/обновлено: {len(groups)}")
    print(f"   Аниме будет сгруппировано: {total_anime_to_group}")

    if not args.yes:
        ans = input("\nПродолжить? (y/n): ").strip().lower()
        if ans != 'y':
            print("Отменено.")
            return

    created_count = 0
    error_count = 0

    print("\n🚀 Начинаю обработку...\n")
    
    for base_name, entries in groups.items():
        try:
            f = create_or_update_franchise(base_name, entries)
            created_count += 1
            if created_count <= 10 or created_count % 50 == 0:
                print(f"  ✓ [{created_count}/{len(groups)}] «{f.name}» ({len(entries)} аниме)")
        except Exception as e:
            error_count += 1
            print(f"  ✗ Ошибка «{base_name}»: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60)
    print(f"  Создано/обновлено франшиз : {created_count}")
    print(f"  Ошибок                    : {error_count}")
    print(f"  Всего франшиз в БД        : {Franchise.objects.count()}")
    print(f"  Аниме во франшизах        : {Anime.objects.filter(franchise__isnull=False).count()}")
    print("=" * 60)


if __name__ == '__main__':
    run()