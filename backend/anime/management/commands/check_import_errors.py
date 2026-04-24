import os
import sys
import django
from django.core.management.base import BaseCommand

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from anime.models import Anime
from django.db.models import Count


class Command(BaseCommand):
    help = "Check for import errors in anime data"

    def handle(self, *args, **options):
        self.stdout.write("Проверка ошибок импорта аниме...")

        # Найти аниме без названия
        empty_titles = Anime.objects.filter(title_ru="")
        if empty_titles.exists():
            self.stdout.write(
                f"Найдено {empty_titles.count()} аниме без русского названия:"
            )
            for anime in empty_titles[:10]:
                self.stdout.write(
                    f"  ID {anime.id}: {anime.title_en or anime.title_jp}"
                )

        # Найти дубликаты по shikimori_id
        duplicates = (
            Anime.objects.values("shikimori_id")
            .annotate(count=Count("id"))
            .filter(count__gt=1, shikimori_id__isnull=False)
        )

        if duplicates.exists():
            self.stdout.write(f"Найдено {len(duplicates)} дубликатов по shikimori_id:")
            for dup in duplicates[:5]:
                animes = Anime.objects.filter(shikimori_id=dup["shikimori_id"])
                self.stdout.write(
                    f"  shikimori_id {dup['shikimori_id']}: {animes.count()} записей"
                )

        # Найти анонсы без года
        announcements_without_year = Anime.objects.filter(
            status="announced", year__isnull=True
        )
        if announcements_without_year.exists():
            self.stdout.write(
                f"Найдено {announcements_without_year.count()} анонсов без года"
            )

        self.stdout.write("Проверка завершена")
