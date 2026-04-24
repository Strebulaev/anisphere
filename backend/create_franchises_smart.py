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
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

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
        return ""
    return " ".join(title.lower().split())


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
        return ""

    # Убираем квадратные скобки [TV], [Dub] и т.д.
    title = re.sub(r"\s*\[[^\]]*\]\s*", " ", title)

    # Убираем круглые скобки с годом, типом, рейтингом
    title = re.sub(
        r"\s*\(\s*(TV|TV-\d+|OVA|Movie|ONA|Special|OVA|ONA|Special|\d{4}|\d{4}-\d{4}|\d{2}[-+])\s*\)\s*",
        " ",
        title,
        flags=re.IGNORECASE,
    )

    # Убираем OVA/ONA/Movie/3D/2D в конце без скобок
    title = re.sub(
        r"\s+(OVA|ONA|Movie|Special|TV|3D|2D)\s*$", " ", title, flags=re.IGNORECASE
    )

    # Убираем ". Фильм" в конце
    title = re.sub(r"\s*\.?\s*Фильм\s*$", " ", title, flags=re.IGNORECASE)

    # Убираем лишние пробелы
    title = " ".join(title.split())

    return title


# ============================================================================
# 2. ИЗВЛЕЧЕНИЕ ЯДРА ФРАНШИЗЫ
# ============================================================================


def normalize_franchise_name(name: str) -> str:
    """
    Нормализует название франшизы для унификации вариаций.
    """
    if not name:
        return name

    # Специальные замены для известных франшиз
    replacements = {
        "ван пис": "ван-пис",
        "ванпис": "ван-пис",
        "one piece": "ван-пис",
        "one-piece": "ван-пис",
        # Добавить другие если нужно
    }

    name_lower = name.lower()
    for old, new in replacements.items():
        name_lower = name_lower.replace(old, new)

    return name_lower


def normalize_title_for_similarity(title: str) -> str:
    """Нормализует название для сравнения: убирает пробелы, тире, пунктуацию."""
    # Убираем пробелы, тире, подчёркивания
    normalized = re.sub(r"[\s\-_]", "", title.lower())
    # Убираем пунктуацию
    normalized = re.sub(r"[^\w]", "", normalized)
    return normalized


def calculate_similarity(title_a: str, title_b: str) -> float:
    """Вычисляет схожесть названий на основе SequenceMatcher."""
    norm_a = normalize_title_for_similarity(title_a)
    norm_b = normalize_title_for_similarity(title_b)
    if not norm_a or not norm_b:
        return 0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def extract_franchise_core(title: str) -> str:
    """
    Извлекает ядро франшизы из названия.

    Более строгий алгоритм: берёт первые 2-3 слова, нормализует.
    """
    if not title:
        return ""

    # Сначала чистим от годов и типов
    cleaned = clean_title_for_core(title)

    # Разделители
    separators = [":", ".", " — ", " - "]

    for sep in separators:
        if sep in cleaned:
            core = cleaned.split(sep)[0].strip()
            if len(core.split()) >= 2:  # Минимум 2 слова
                return normalize_franchise_name(core)

    # Без разделителей: берём первые 2-3 слова
    words = cleaned.split()
    if len(words) >= 3:
        core = " ".join(words[:3])
    elif len(words) == 2:
        core = " ".join(words)
    else:
        core = words[0] if words else ""

    return normalize_franchise_name(core)


def get_franchise_priority_name(titles: list[str]) -> str:
    """
    Выбирает лучшее название для франшизы из списка названий аниме.

    Приоритет:
    1. Самое короткое название (обычно основное)
    2. Без подзаголовков (без двоеточия)
    3. С максимальным количеством слов
    """
    if not titles:
        return ""

    # Сортируем: сначала без двоеточий, потом по длине
    def score(title):
        has_colon = 1 if ":" in title else 0
        length = len(title)
        return (has_colon, length)

    sorted_titles = sorted(titles, key=score)
    return sorted_titles[0]


# ============================================================================
# 3. ГРУППИРОВКА
# ============================================================================


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, p):
        if self.parent[p] != p:
            self.parent[p] = self.find(self.parent[p])
        return self.parent[p]

    def union(self, p, q):
        rootP = self.find(p)
        rootQ = self.find(q)
        if rootP == rootQ:
            return
        if self.rank[rootP] < self.rank[rootQ]:
            self.parent[rootP] = rootQ
        elif self.rank[rootP] > self.rank[rootQ]:
            self.parent[rootQ] = rootP
        else:
            self.parent[rootQ] = rootP
            self.rank[rootP] += 1


# Стоп-слова: не использовать для группировки
STOP_WORDS = {
    "тв",
    "tv",
    "ova",
    "movie",
    "фильм",
    "сезон",
    "часть",
    "эпизод",
    "special",
    "ona",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "i",
    "ii",
    "iii",
    "iv",
    "v",
    "vi",
    "vii",
    "viii",
    "ix",
    "x",
    "первый",
    "второй",
    "третий",
    "четвёртый",
    "пятый",
    "серия",
    "серии",
    "эп",
    "eps",
    "ep",
    "и",
    "в",
    "на",
    "с",
    "по",
    "для",
    "из",
    "к",
    "от",
    "до",
    "за",
    "при",
    "под",
    "над",
}


def get_significant_words(title: str) -> set[str]:
    """Извлекает значимые слова из названия, исключая стоп-слова."""
    words = set()
    for word in title.lower().split():
        word = re.sub(r"[^\w\-]", "", word)  # Убираем пунктуацию
        if word and word not in STOP_WORDS and len(word) > 2:
            words.add(word)
    return words


def group_anime_into_franchises():
    """
    Группирует аниме по схожести названий (fuzzy matching с фильтром стоп-слов).
    """
    print("📊 Группировка аниме по франшизам (fuzzy matching)...")

    # Получаем все аниме с русскими названиями
    animes = list(
        Anime.objects.filter(title_ru__isnull=False)
        .exclude(title_ru="")
        .only("id", "title_ru")
    )
    n = len(animes)

    if n == 0:
        return {}

    # Shikimori prefixes
    shiki_prefixes = []
    for anime in animes:
        prefix = str(anime.shikimori_id)[:4] if anime.shikimori_id else ""
        shiki_prefixes.append(prefix)

    # Union-Find для группировки
    uf = UnionFind(n)

    # Сначала группируем по shikimori_id префиксу (точная группировка)
    prefix_groups = defaultdict(list)
    for i, prefix in enumerate(shiki_prefixes):
        if prefix:
            prefix_groups[prefix].append(i)

    for indices in prefix_groups.values():
        if len(indices) >= 2:
            for i in range(1, len(indices)):
                uf.union(indices[0], indices[i])

    # Затем fuzzy matching: сравниваем все пары с similarity >= 0.7
    # Но чтобы не было O(n^2), сравниваем только если длина названий близка
    for i, anime_a in enumerate(animes):
        title_a = anime_a.title_ru
        len_a = len(title_a.split())

        for j, anime_b in enumerate(animes):
            if i >= j or uf.find(i) == uf.find(j):
                continue

            title_b = anime_b.title_ru
            len_b = len(title_b.split())

            # Пропускаем если длины слишком разные
            if abs(len_a - len_b) > 2:
                continue

            similarity = calculate_similarity(title_a, title_b)
            if similarity >= 0.7:
                uf.union(i, j)

    # Собираем группы
    groups = defaultdict(list)
    for i, anime in enumerate(animes):
        root = uf.find(i)
        groups[root].append(anime.id)

    # Фильтруем группы с 2+ аниме
    multi_anime = {f"group_{k}": v for k, v in groups.items() if len(v) >= 2}

    print(f"  Найдено {len(multi_anime)} франшиз")

    # Статистика
    sizes = defaultdict(int)
    for ids in multi_anime.values():
        sizes[len(ids)] += 1

    print("  Распределение по размеру:")
    for size in sorted(sizes.keys()):
        print(f"    {size} аниме: {sizes[size]} франшиз")

    return multi_anime


# ============================================================================
# 4. СОЗДАНИЕ ФРАНШИЗ В БД
# ============================================================================


def unbind_and_delete_franchises():
    """
    Отвязывает все аниме от франшиз и удаляет франшизы.
    """
    print("🔄 Отвязываем аниме от франшиз...")

    # Отвязываем аниме
    unbound_count = Anime.objects.filter(franchise__isnull=False).update(franchise=None)
    print(f"  Отвязано аниме: {unbound_count}")

    # Удаляем франшизы
    old_count = Franchise.objects.count()
    if old_count > 0:
        Franchise.objects.all().delete()
        print(f"  Удалено франшиз: {old_count}")


@transaction.atomic
def create_franchises_from_groups(core_groups: dict[str, list[int]]):
    """
    Создаёт франшизы в БД и привязывает аниме.
    """
    print("\n📁 Создание франшиз в БД...")

    created_count = 0
    updated_count = 0
    error_count = 0

    for core, anime_ids in core_groups.items():
        try:
            # Получаем аниме для франшизы
            animes = list(Anime.objects.filter(id__in=anime_ids).order_by("year", "id"))
            titles = [a.title_ru for a in animes]

            # Выбираем лучшее название для франшизы
            franchise_name = get_franchise_priority_name(titles)

            # Находим poster: poster первого аниме с poster (не poster_url)
            poster = None
            for anime in animes:
                if anime.poster:  # ImageField, не пустой
                    poster = anime.poster
                    break

            # Создаём франшизу
            franchise = Franchise.objects.create(
                name=franchise_name,
                description=f'Франшиза "{franchise_name}"',
                poster=poster,  # Устанавливаем poster из первого аниме
            )

            # Привязываем аниме к франшизе и устанавливаем порядок
            for order, anime in enumerate(animes, 1):
                anime.franchise = franchise
                anime.franchise_order = order
                anime.save(update_fields=["franchise", "franchise_order"])

            created_count += 1

            # Прогресс каждые 100
            if created_count % 100 == 0:
                print(f"  Обработано {created_count} франшиз...")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f'Error creating franchise for core "{core}": {e}'
            )
            error_count += 1

    print(f"\n✅ Франшизы созданы:")
    print(f"  Создано: {created_count}")
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
        titles = list(
            Anime.objects.filter(id__in=anime_ids).values_list("title_ru", flat=True)[
                :5
            ]
        )

        # Выбираем название франшизы
        franchise_name = get_franchise_priority_name(titles)

        print(f"\n📁 {franchise_name.upper()} ({len(anime_ids)} аниме)")
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

    stats = Franchise.objects.annotate(anime_count=Count("entries")).order_by(
        "-anime_count"
    )[:20]

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

    # Шаг 0: Отвязываем и удаляем старые франшизы
    unbind_and_delete_franchises()

    # Шаг 1: Группировка
    core_groups = group_anime_into_franchises()

    # Шаг 2: Показываем примеры
    print_franchise_examples(core_groups)

    # Шаг 3: Спрашиваем подтверждение
    print("\n" + "=" * 60)
    print("СОЗДАТЬ ФРАНШИЗЫ В БД?")
    print("=" * 60)
    print("Это создаст новые франшизы с постерами из первых аниме.")
    print()
    response = input("Продолжить? (yes/no): ").strip().lower()

    if response != "yes":
        print("❌ Отменено")
        return

    # Шаг 4: Создаём франшизы
    create_franchises_from_groups(core_groups)

    # Шаг 5: Проверка
    verify_franchises()

    print("\n✅ Готово!")


if __name__ == "__main__":
    main()
