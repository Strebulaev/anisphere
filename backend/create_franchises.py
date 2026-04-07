import os
import sys
import re
from collections import defaultdict

# Настройка Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime, Franchise


def extract_base_title(title: str) -> str | None:
    """
    Извлекает базовое название из полного названия аниме.
    
    Возвращает первые 3-4 слова (основная часть названия).
    Исключает в скобках: [ТВ-1], (ТВ), [Фильм], (OVA), и т.д.
    
    Примеры:
    - "Добро пожаловать в ад, Ирума [ТВ-1]" -> "добро пожаловать в ад ирума"
    - "Добро пожаловать в Эн.Эйч.Кэй" -> "добро пожаловать в эн эйч кэй"
    - "Наруто [ТВ-1]" -> "наруто"
    """
    if not title:
        return None
    
    # Убираем всё в квадратных скобках и круглых скобках (типы аниме)
    cleaned = re.sub(r'\[.*?\]', '', title)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    
    # Убираем всякие знаки препинания, оставляем только буквы и пробелы
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    
    # Разбиваем на слова и убираем пустые
    words = [w for w in cleaned.split() if w]
    
    if len(words) < 2:
        return None
    
    # Если слово содержит только цифры (номер сезона/серии) - убираем его и всё после
    filtered_words = []
    for w in words:
        # Если слово - только цифры, останавливаемся
        if re.match(r'^[\d]+$', w):
            break
        # Если слово содержит номер (типа TV1, TV2) - тоже останавливаемся
        if re.match(r'^(тв|tv|сезон|season)\s*[\d]*$', w.lower()):
            break
        filtered_words.append(w)
    
    # Минимум 3 слова для уникальной идентификации (чтобы не объединять "Добро пожаловать в")
    if len(filtered_words) < 3:
        return None
    
    # Берём первые 4 слова максимум
    base_words = filtered_words[:4]
    
    return ' '.join(base_words).lower()


def extract_season_number(title: str) -> int:
    """Извлекает номер сезона/части из названия."""
    patterns = [
        r'\[ТВ-?(\d+)\]',      # [ТВ-1], [ТВ 1]
        r'\[(\d+) сезон\]',    # [1 сезон]
        r'\(ТВ-?(\d+)\)',      # (ТВ-1)
        r'\[Часть (\d+)\]',    # [Часть 1]
        r'\[Фильм (\d+)\]',    # [Фильм 1]
        r'\[OVA (\d+)\]',      # [OVA 1]
        r'(?:ТВ|tv)\s*(\d+)',  # ТВ 1
        r'сезон\s*(\d+)',      # сезон 1
        r'\s(\d+)$',           # в конце число
    ]
    
    title_lower = title.lower()
    for pattern in patterns:
        match = re.search(pattern, title_lower)
        if match:
            return int(match.group(1))
    
    return 1  # По умолчанию первый сезон


def get_sort_key(anime):
    """Ключ сортировки для аниме внутри франшизы."""
    season = extract_season_number(anime.title_ru or anime.title_en or '')
    year = anime.year or 0
    # Сортируем по сезону, потом по году
    return (season, year)


def create_franchises():
    """Создаёт франшизы на основе названий аниме."""
    
    print("=" * 60)
    print("СОЗДАНИЕ ФРАНШИЗ ИЗ АНИМЕ")
    print("=" * 60)
    
    # Получаем все аниме без франшизы
    all_anime = list(Anime.objects.filter(franchise__isnull=True).select_related())
    print(f"Всего аниме без франшизы: {len(all_anime)}")
    
    # Группируем по базовому названию
    groups = defaultdict(list)
    
    for anime in all_anime:
        # Пробуем оба названия
        base = extract_base_title(anime.title_ru) or extract_base_title(anime.title_en)
        if base:
            groups[base].append(anime)
    
    # Фильтруем группы с более чем одним аниме
    franchise_groups = {k: v for k, v in groups.items() if len(v) > 1}
    
    print(f"Найдено групп для объединения: {len(franchise_groups)}")
    
    created_count = 0
    total_anime_processed = 0
    
    for base_name, anime_list in sorted(franchise_groups.items(), key=lambda x: -len(x[1])):
        # Сортируем по сезону/году
        anime_list.sort(key=get_sort_key)
        
        # Формируем название франшизы (первое аниме без номера сезона)
        first_title = anime_list[0].title_ru or anime_list[0].title_en or 'Без названия'
        # Убираем [ТВ-1] и т.д. из названия для красоты
        franchise_name = re.sub(r'\s*\[.*?\]', '', first_title)
        franchise_name = re.sub(r'\s*\(.*?\)', '', franchise_name).strip()
        
        # Если название получилось пустым, используем base_name
        if not franchise_name:
            franchise_name = base_name.title()
        
        print(f"\n📦 Франшиза: {franchise_name}")
        print(f"   Частей: {len(anime_list)}")
        
        # Создаём франшизу (обрабатываем случай если уже есть)
        existing_franchises = Franchise.objects.filter(name=franchise_name)
        if existing_franchises.exists():
            franchise = existing_franchises.first()
            print(f"   🔄 Использована существующая франшиза (ID: {franchise.id})")
        else:
            franchise = Franchise.objects.create(
                name=franchise_name,
                description=f'Автоматически созданная франшиза из {len(anime_list)} аниме',
            )
            print(f"   ✅ Создана новая франшиза (ID: {franchise.id})")
        
        # Привязываем аниме к франшизе
        for order, anime in enumerate(anime_list, 1):
            old_franchise = anime.franchise
            anime.franchise = franchise
            anime.franchise_order = order
            anime.save(update_fields=['franchise', 'franchise_order'])
            
            if old_franchise:
                old_franchise.update_aggregated_data()
            
            title_short = (anime.title_ru or anime.title_en)[:40]
            print(f"      {order}. {title_short} (ID: {anime.id})")
        
        # Обновляем агрегированные данные франшизы (без parts_count)
        entries = list(franchise.entries.all())
        if entries:
            scores = [e.score for e in entries if e.score]
            franchise.score = sum(scores) / len(scores) if scores else None
            years = [e.year for e in entries if e.year]
            if years:
                franchise.year_start = min(years)
                franchise.year_end = max(years)
            all_genres = set()
            for e in entries:
                if e.genres:
                    all_genres.update(e.genres)
            franchise.genres = list(all_genres)
            franchise.save(update_fields=['score', 'year_start', 'year_end', 'genres'])
        
        created_count += 1
        total_anime_processed += len(anime_list)
    
    print("\n" + "=" * 60)
    print(f"ГОТОВО!")
    print(f"Создано/обновлено франшиз: {created_count}")
    print(f"Обработано аниме: {total_anime_processed}")
    print("=" * 60)
    
    return created_count, total_anime_processed


def show_stats():
    """Показывает статистику по франшизам."""
    print("\n📊 СТАТИСТИКА ФРАНШИЗ")
    print("-" * 40)
    
    franchises = Franchise.objects.annotate(
        parts_count_count=models.Count('entries')
    ).order_by('-parts_count_count')
    
    for f in franchises[:20]:
        print(f"  {f.name[:45]:<45} | {f.parts_count_count} частей")
    
    total = Franchise.objects.count()
    print(f"\nВсего франшиз: {total}")


if __name__ == '__main__':
    import django
    from django.db import models
    
    # Запускаем создание
    create_franchises()
    
    # Показываем статистику
    show_stats()
