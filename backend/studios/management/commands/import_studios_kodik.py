"""
Management command: import_studios_kodik

Импортирует все аниме-студии из Kodik API (/list с with_material_data=true).
Для каждой студии собирает список аниме, которые она выпустила.

Использование:
    python manage.py import_studios_kodik
    python manage.py import_studios_kodik --limit 500
    python manage.py import_studios_kodik --reset   # очистить и начать заново
"""

import time
import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from studios.models import Studio, StudioAnime
from anime.kodik_config import KODIK_API_TOKEN, KODIK_API_BASE


KODIK_TOKEN = KODIK_API_TOKEN
KODIK_LIST_URL = f'{KODIK_API_BASE}/list'


def transliterate_slug(name: str) -> str:
    """
    Генерирует slug из названия студии.
    Для ASCII-имён (Studio Deen, J.C.Staff) работает django slugify.
    Для японских — транслитерируем вручную.
    """
    ru_en = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    lower = name.lower()
    result = ''
    for ch in lower:
        result += ru_en.get(ch, ch)
    slug = slugify(result)
    if not slug:
        slug = f'studio-{abs(hash(name)) % 100000}'
    return slug


class Command(BaseCommand):
    help = 'Импортирует студии и их аниме из Kodik API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Количество записей за один запрос к Kodik (макс 100)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить все студии и начать импорт заново',
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=0,
            help='Максимальное количество страниц (0 = все)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Удаляем все студии...'))
            StudioAnime.objects.all().delete()
            Studio.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Студии удалены.'))

        limit = min(options['limit'], 100)
        max_pages = options['max_pages']

        # Словарь: studio_name -> {аниме данные}
        # {
        #   "Studio MAPPA": {
        #     "anime": [{"shikimori_id": ..., "title": ..., ...}, ...],
        #     "total": 0
        #   }
        # }
        studio_data: dict[str, dict] = {}

        # --- Шаг 1: собираем все аниме из Kodik ---
        self.stdout.write(self.style.HTTP_INFO(
            f'Начинаем парсинг Kodik API (limit={limit})...'
        ))

        url = KODIK_LIST_URL
        params = {
            'token': KODIK_TOKEN,
            'limit': limit,
            'types': 'anime,anime-serial',
            'with_material_data': 'true',
            'sort': 'updated_at',
            'order': 'desc',
        }

        page_num = 0
        total_items = 0
        total_kodik = None

        while url:
            page_num += 1
            if max_pages and page_num > max_pages:
                self.stdout.write(self.style.WARNING(
                    f'Достигнут лимит страниц ({max_pages}). Останавливаемся.'
                ))
                break

            try:
                resp = requests.get(url, params=params if page_num == 1 else None, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка запроса (стр. {page_num}): {e}'))
                time.sleep(2)
                continue

            if total_kodik is None:
                total_kodik = data.get('total', '?')
                self.stdout.write(f'Всего материалов в Kodik: {total_kodik}')

            results = data.get('results', [])
            if not results:
                break

            for item in results:
                md = item.get('material_data') or {}
                anime_studios = md.get('anime_studios') or []

                if not anime_studios:
                    continue

                # Данные об аниме
                anime_info = {
                    'kodik_id': item.get('id', ''),
                    'title': (
                        md.get('anime_title')
                        or md.get('title')
                        or item.get('title', '')
                    ),
                    'title_en': md.get('title_en', ''),
                    'title_orig': item.get('title_orig', ''),
                    'year': item.get('year') or md.get('year'),
                    'kind': md.get('anime_kind', item.get('type', 'tv')),
                    'status': md.get('anime_status') or md.get('all_status', ''),
                    'shikimori_id': item.get('shikimori_id', ''),
                    'poster': (
                        md.get('anime_poster_url')
                        or md.get('poster_url', '')
                    ),
                    'score': md.get('shikimori_rating'),
                    'episodes': md.get('episodes_total'),
                    'genres': md.get('anime_genres') or md.get('all_genres') or [],
                    'description': (
                        md.get('anime_description')
                        or md.get('description', '')
                    ),
                }

                for studio_name in anime_studios:
                    studio_name = studio_name.strip()
                    if not studio_name:
                        continue
                    if studio_name not in studio_data:
                        studio_data[studio_name] = {'anime': []}
                    # Не дублируем по kodik_id
                    existing_ids = {a['kodik_id'] for a in studio_data[studio_name]['anime']}
                    if anime_info['kodik_id'] not in existing_ids:
                        studio_data[studio_name]['anime'].append(anime_info)

                total_items += 1

            self.stdout.write(
                f'  Стр. {page_num}: обработано {total_items} аниме, '
                f'студий найдено: {len(studio_data)}'
            )

            # Следующая страница
            next_page = data.get('next_page')
            if next_page:
                url = next_page
                params = None  # params уже в next_page URL
                time.sleep(0.3)  # вежливая пауза
            else:
                break

        self.stdout.write(self.style.SUCCESS(
            f'\nПарсинг завершён. Аниме: {total_items}, Студий: {len(studio_data)}'
        ))

        # --- Шаг 2: сохраняем студии в БД ---
        self.stdout.write(self.style.HTTP_INFO('\nСохраняем студии в БД...'))

        created_count = 0
        updated_count = 0
        anime_linked = 0

        for studio_name, sdata in studio_data.items():
            anime_list = sdata['anime']

            # Генерируем slug
            slug_candidate = transliterate_slug(studio_name)

            # Создаём или обновляем студию
            studio, was_created = Studio.objects.get_or_create(
                name=studio_name,
                defaults={'slug': slug_candidate}
            )

            # Если slug пустой (старые записи без slug)
            if not studio.slug:
                studio.slug = slug_candidate
                studio.save(update_fields=['slug'])

            if was_created:
                created_count += 1
            else:
                updated_count += 1

            # --- Дедупликация по shikimori_id перед подсчётом статистики ---
            # Одно аниме может быть импортировано несколько раз (разные озвучки/kodik_id)
            # Оставляем одну запись на shikimori_id (с наибольшим score для надёжности)
            unique_map: dict[str, dict] = {}  # shikimori_id -> лучший вариант
            no_shiki: list[dict] = []
            for a in anime_list:
                sid = a.get('shikimori_id', '').strip()
                if sid:
                    prev = unique_map.get(sid)
                    if prev is None or (a.get('score') or 0) > (prev.get('score') or 0):
                        unique_map[sid] = a
                else:
                    # Без shikimori_id — дедуплицируем по заголовку
                    title_key = (a.get('title') or '').strip().lower()
                    if title_key not in {(x.get('title') or '').lower() for x in no_shiki}:
                        no_shiki.append(a)
            unique_anime = list(unique_map.values()) + no_shiki

            # Статистика по уникальным аниме
            tv_count = sum(1 for a in unique_anime if a['kind'] in ('tv', 'tv_13', 'tv_24', 'tv_48'))
            movie_count = sum(1 for a in unique_anime if a['kind'] == 'movie')
            ova_count = sum(1 for a in unique_anime if a['kind'] in ('ova', 'ona', 'special'))

            scores = [a['score'] for a in unique_anime if a.get('score')]
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

            # Жанровая статистика — считаем по уникальным аниме
            total_unique = len(unique_anime) or 1
            genre_raw: dict[str, int] = {}
            for a in unique_anime:
                for g in (a.get('genres') or []):
                    genre_raw[g] = genre_raw.get(g, 0) + 1
            # Сохраняем как процент от уникальных аниме (не суммарный, а доля 0-100)
            genre_counter = {
                g: round(cnt / total_unique * 100)
                for g, cnt in genre_raw.items()
            }

            # Топ-5 работ по рейтингу
            top5 = sorted(
                [a for a in unique_anime if a.get('title')],
                key=lambda x: x.get('score') or 0,
                reverse=True
            )[:5]
            notable = [a['title'] for a in top5]

            # Обновляем поля студии
            studio.total_anime = len(unique_anime)
            studio.tv_count = tv_count
            studio.movie_count = movie_count
            studio.ova_count = ova_count
            studio.average_rating = avg_score
            studio.notable_works = notable
            studio.genre_stats = genre_counter
            studio.is_active = True
            studio.save()

            # Сохраняем связи с аниме
            for a in anime_list:
                title = a.get('title') or a.get('title_orig') or '—'
                kind = a.get('kind', 'tv')
                # Нормализуем тип
                kind_map = {
                    'tv_13': 'tv', 'tv_24': 'tv', 'tv_48': 'tv',
                    'anime-serial': 'tv', 'anime': 'tv',
                }
                kind = kind_map.get(kind, kind)[:20]

                year = a.get('year')
                if year:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = None

                score = a.get('score')
                if score:
                    try:
                        score = float(score)
                    except (ValueError, TypeError):
                        score = None

                # Ищем аниме в нашей БД по shikimori_id
                anime_db_id = None
                shiki_id = a.get('shikimori_id', '')
                if shiki_id:
                    try:
                        from anime.models import Anime as AnimeModel
                        db_anime = AnimeModel.objects.filter(
                            shikimori_id=str(shiki_id)
                        ).first()
                        if db_anime:
                            anime_db_id = db_anime.pk
                    except Exception:
                        pass

                StudioAnime.objects.update_or_create(
                    studio=studio,
                    kodik_id=a['kodik_id'],
                    defaults={
                        'anime_db_id': anime_db_id,
                        'anime_title': title[:255],
                        'anime_title_en': (a.get('title_en') or '')[:255],
                        'anime_kind': kind,
                        'anime_year': year,
                        'anime_score': score,
                        'anime_poster': (a.get('poster') or '')[:500],
                        'anime_status': (a.get('status') or '')[:50],
                        'shikimori_id': str(shiki_id)[:50],
                        'episodes_total': a.get('episodes'),
                        'description': (a.get('description') or '')[:2000],
                        'genres': a.get('genres') or [],
                    }
                )
                anime_linked += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Готово!\n'
            f'   Создано студий:  {created_count}\n'
            f'   Обновлено:       {updated_count}\n'
            f'   Аниме привязано: {anime_linked}\n'
            f'   Всего в БД:      {Studio.objects.count()}'
        ))
