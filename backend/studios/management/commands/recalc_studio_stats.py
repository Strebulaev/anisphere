"""
Management command: recalc_studio_stats

Пересчитывает статистику студий (total_anime, жанры, рейтинг) по данным
которые уже есть в таблице StudioAnime, с дедупликацией по shikimori_id.

Использование:
    python manage.py recalc_studio_stats
    python manage.py recalc_studio_stats --studio "Studio MAPPA"
"""

from django.core.management.base import BaseCommand
from django.db.models import Avg
from studios.models import Studio, StudioAnime


class Command(BaseCommand):
    help = 'Пересчитывает статистику студий с дедупликацией по shikimori_id'

    def add_arguments(self, parser):
        parser.add_argument(
            '--studio',
            type=str,
            default='',
            help='Пересчитать только конкретную студию (по имени)',
        )

    def handle(self, *args, **options):
        studio_filter = options.get('studio', '').strip()

        qs = Studio.objects.filter(is_active=True)
        if studio_filter:
            qs = qs.filter(name__icontains=studio_filter)

        total = qs.count()
        self.stdout.write(f'Пересчитываем статистику для {total} студий...\n')

        updated = 0
        for studio in qs.iterator():
            anime_qs = StudioAnime.objects.filter(studio=studio)

            # --- Дедупликация по shikimori_id ---
            seen_shiki: set[str] = set()
            seen_titles: set[str] = set()
            unique: list[StudioAnime] = []

            for a in anime_qs.order_by('-anime_score'):
                sid = (a.shikimori_id or '').strip()
                if sid:
                    if sid not in seen_shiki:
                        seen_shiki.add(sid)
                        unique.append(a)
                else:
                    title_key = (a.anime_title or '').strip().lower()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        unique.append(a)

            total_unique = len(unique) or 1

            # Счётчики типов
            TV_KINDS = {'tv', 'tv_13', 'tv_24', 'tv_48'}
            OVA_KINDS = {'ova', 'ona', 'special', 'tv_special', 'music'}
            tv_count = sum(1 for a in unique if a.anime_kind in TV_KINDS)
            movie_count = sum(1 for a in unique if a.anime_kind == 'movie')
            ova_count = sum(1 for a in unique if a.anime_kind in OVA_KINDS)

            # Средний рейтинг
            scores = [a.anime_score for a in unique if a.anime_score is not None]
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

            # Жанровая статистика — доля аниме с каждым жанром (0–100%)
            genre_raw: dict[str, int] = {}
            for a in unique:
                for g in (a.genres or []):
                    if g:
                        genre_raw[g] = genre_raw.get(g, 0) + 1
            genre_stats = {
                g: round(cnt / total_unique * 100)
                for g, cnt in genre_raw.items()
            }

            # Топ-5 работ
            top5 = sorted(
                [a for a in unique if a.anime_title],
                key=lambda x: x.anime_score or 0,
                reverse=True
            )[:5]
            notable = [a.anime_title for a in top5]

            # Сохраняем
            Studio.objects.filter(pk=studio.pk).update(
                total_anime=total_unique,
                tv_count=tv_count,
                movie_count=movie_count,
                ova_count=ova_count,
                average_rating=avg_score,
                notable_works=notable,
                genre_stats=genre_stats,
            )

            updated += 1
            if updated % 50 == 0:
                self.stdout.write(f'  Обработано: {updated}/{total}...')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Готово! Пересчитано студий: {updated}'
        ))
