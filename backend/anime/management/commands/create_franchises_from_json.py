import os
import json
import django
from django.core.management.base import BaseCommand
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from anime.models import Anime, Franchise


class Command(BaseCommand):
    help = "Создание франшиз из файла franshize_anime.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            nargs="?",
            default="franshize_anime.json",
            help="Путь к JSON-файлу с франшизами",
        )

    def handle(self, *args, **options):
        json_path = options["json_path"]

        if not os.path.isabs(json_path):
            json_path = os.path.join(settings.BASE_DIR, "..", json_path)

        json_path = os.path.abspath(json_path)

        if not os.path.exists(json_path):
            self.stderr.write(f"Файл не найден: {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        created_count = 0
        skipped_count = 0
        not_found = []

        for item in data.get("franchises", []):
            name = item.get("name")
            titles = [t.strip() for t in item.get("titles", []) if t.strip()]

            if not name or not titles:
                continue

            franchise = Franchise.objects.filter(name__iexact=name).first()
            if franchise:
                skipped_count += 1
            else:
                franchise = Franchise.objects.create(
                    name=name,
                    description=f"Франшиза: {name}",
                )
                created_count += 1

            matched_anime = Anime.objects.filter(title_ru__in=titles)

            unmatched = [t for t in titles if not matched_anime.filter(title_ru=t).exists()]
            if unmatched:
                not_found.extend(unmatched)

            order = 1
            for anime in matched_anime.order_by("year"):
                anime.franchise = franchise
                anime.franchise_order = order
                anime.save(update_fields=["franchise", "franchise_order"])
                order += 1

            franchise.update_aggregated_data()

        self.stdout.write(f"Создано франшиз: {created_count}")
        self.stdout.write(f"Пропущено (уже есть): {skipped_count}")

        if not_found:
            self.stdout.write(f"Не найдено в каталоге ({len(not_found)} позиций):")
            for title in not_found[:20]:
                self.stdout.write(f"  - {title}")
            if len(not_found) > 20:
                self.stdout.write(f"  ... и ещё {len(not_found) - 20}")
