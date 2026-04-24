import os
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from anime.models import Anime, Franchise
from users.models import User


class Command(BaseCommand):
    help = "Import anime data from Jikan API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Limit number of anime to import per endpoint",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting Jikan import...")

        limit = options["limit"]

        # Import current season
        self.import_season("now", limit=limit)

        # Import upcoming anime (announcements)
        self.import_upcoming(limit=limit)

        self.stdout.write("Import completed")

    def import_season(self, year, season=None, limit=100):
        """Import anime from a specific season"""
        if season:
            url = f"https://api.jikan.moe/v4/seasons/{year}/{season}"
        else:
            url = f"https://api.jikan.moe/v4/seasons/{year}"

        self.stdout.write(f"Importing {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            anime_list = data.get("data", [])
            for anime_data in anime_list[:limit]:
                self.import_anime(anime_data)

            time.sleep(1)  # Rate limit
        except Exception as e:
            self.stderr.write(f"Error importing season {year}-{season}: {e}")

    def import_upcoming(self, limit=200):
        """Import upcoming anime (announcements)"""
        url = "https://api.jikan.moe/v4/seasons/upcoming"
        self.stdout.write(f"Importing upcoming announcements: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            anime_list = data.get("data", [])
            for anime_data in anime_list[:limit]:
                self.import_anime(anime_data)

            time.sleep(1)
        except Exception as e:
            self.stderr.write(f"Error importing upcoming: {e}")

    def import_anime(self, data):
        """Import single anime from Jikan data"""
        mal_id = data.get("mal_id")
        if not mal_id:
            return

        title_ru = data.get("title")
        title_en = data.get("title_english")
        title_jp = data.get("title_japanese")

        synopsis = data.get("synopsis", "")
        year = data.get("year")
        episodes = data.get("episodes")
        score = data.get("score")
        status = data.get("status")  # Finished Airing, Currently Airing, Not yet aired

        # Map status
        if status == "Finished Airing":
            anime_status = "finished"
        elif status == "Currently Airing":
            anime_status = "ongoing"
        elif status == "Not yet aired":
            anime_status = "announced"
        else:
            anime_status = "announced"

        # Genres
        genres = [g["name"] for g in data.get("genres", [])]
        genres_str = ",".join(genres)

        # Studios
        studios = [s["name"] for s in data.get("studios", [])]
        studios_str = ",".join(studios)

        # Images
        images = data.get("images", {})
        poster_url = images.get("jpg", {}).get("large_image_url") or images.get(
            "jpg", {}
        ).get("image_url")

        with transaction.atomic():
            defaults = {
                "title_ru": title_ru or "",
                "data_source": "jikan",
            }

            if title_en:
                defaults["title_en"] = title_en
            if title_jp:
                defaults["title_jp"] = title_jp
            if synopsis:
                defaults["description"] = synopsis
            if year:
                defaults["year"] = year
            if episodes:
                defaults["episodes"] = episodes
            if score:
                defaults["score"] = score
            if anime_status:
                defaults["status"] = anime_status
            if genres_str:
                defaults["genres"] = genres_str
            if studios_str:
                defaults["studios"] = studios_str
            if poster_url:
                defaults["poster_url"] = poster_url

            anime, created = Anime.objects.update_or_create(
                mal_id=mal_id, defaults=defaults
            )

            if created:
                self.stdout.write(f"Created anime: {title_ru}")
            else:
                self.stdout.write(f"Updated anime: {title_ru}")

    def clean_old_announcements(self):
        """Remove old announcements that are no longer upcoming"""
        # This could be implemented to remove announcements older than certain date
        pass
