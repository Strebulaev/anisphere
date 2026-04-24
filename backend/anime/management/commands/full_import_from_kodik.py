import os
import sys
import django
from django.core.management.base import BaseCommand
import requests
import time
from datetime import datetime

from anime.models import Anime, Genre, Studio
from django.db import transaction


class Command(BaseCommand):
    help = "Full import of anime from Kodik API"

    KODIK_TOKEN = "74ecb013335271e4344ebc994956dd75"
    KODIK_API_BASE = "https://kodik-api.com"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=100000, help="Limit number of anime to import"
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting full Kodik import...")

        limit = options["limit"]
        all_kodik_anime = self.fetch_all_anime_from_kodik(limit)

        if not all_kodik_anime:
            self.stderr.write("Failed to load data from Kodik")
            return

        self.stdout.write(f"Processing {len(all_kodik_anime)} anime...")

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, kodik_data in enumerate(all_kodik_anime, 1):
            result = self.import_anime_from_kodik_data(kodik_data)

            if result is None:
                error_count += 1
            elif result["created"]:
                created_count += 1
            else:
                updated_count += 1

            if i % 1000 == 0:
                self.stdout.write(
                    f"Processed {i}/{len(all_kodik_anime)} (created: {created_count}, updated: {updated_count}, errors: {error_count})"
                )

            if i % 100 == 0:
                time.sleep(0.1)

        self.stdout.write(
            f"Import completed: created {created_count}, updated {updated_count}, errors {error_count}"
        )

    def fetch_all_anime_from_kodik(self, limit):
        """Fetch all anime from Kodik API via /list endpoint."""
        all_anime = []

        self.stdout.write("Loading anime from Kodik API (/list)...")

        url = f"{self.KODIK_API_BASE}/list"
        params = {
            "token": self.KODIK_TOKEN,
            "limit": 100,
            "types": "anime,anime-serial",
            "with_material_data": "true",
        }

        page = 1
        while len(all_anime) < limit:
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])

                if not results:
                    break

                all_anime.extend(results)
                total = data.get("total", 0)

                self.stdout.write(
                    f"  Page {page}: loaded {len(all_anime)}/{total} anime"
                )

                next_page = data.get("next_page")
                if not next_page:
                    break

                url = next_page
                params = {}
                page += 1
                time.sleep(0.2)

            except Exception as e:
                self.stderr.write(f"Error on page {page}: {e}")
                break

        self.stdout.write(f"Total loaded: {len(all_anime)} anime")
        return all_anime[:limit]

    def import_anime_from_kodik_data(self, kodik_data):
        """Import single anime from Kodik data."""
        try:
            material_data = kodik_data.get("material_data", {})

            if not material_data:
                return None

            shikimori_id = kodik_data.get("shikimori_id")
            if not shikimori_id:
                return None

            shikimori_id = int(shikimori_id)

            title_ru = (
                material_data.get("anime_title") or material_data.get("title") or ""
            )
            title_en = material_data.get("title_en") or ""
            title_jp = (
                material_data.get("other_titles", [""])[0]
                if isinstance(material_data.get("other_titles"), list)
                else ""
            )

            year = None
            if material_data.get("year"):
                try:
                    year = int(material_data.get("year"))
                except (ValueError, TypeError):
                    pass

            status = self.map_status(
                material_data.get("anime_status") or material_data.get("all_status")
            )
            kind = self.map_kind(material_data.get("anime_kind"))

            episodes = material_data.get("episodes_total") or material_data.get(
                "episodes_aired"
            )
            if episodes:
                try:
                    episodes = int(episodes)
                except (ValueError, TypeError):
                    episodes = None

            score = None
            if material_data.get("shikimori_rating"):
                try:
                    score = float(material_data.get("shikimori_rating"))
                except (ValueError, TypeError):
                    pass

            poster_url = (
                material_data.get("anime_poster_url")
                or material_data.get("poster_url")
                or ""
            )
            description = (
                material_data.get("anime_description")
                or material_data.get("description")
                or ""
            )

            genres = (
                material_data.get("anime_genres")
                or material_data.get("all_genres")
                or []
            )
            studios = material_data.get("anime_studios") or []

            mal_id = None
            if material_data.get("mal_id"):
                try:
                    mal_id = int(material_data.get("mal_id"))
                except (ValueError, TypeError):
                    pass

            with transaction.atomic():
                anime, created = Anime.objects.update_or_create(
                    shikimori_id=shikimori_id,
                    defaults={
                        "title_ru": title_ru,
                        "title_en": title_en,
                        "title_jp": title_jp,
                        "description": description,
                        "year": year,
                        "status": status,
                        "kind": kind,
                        "episodes": episodes,
                        "score": score,
                        "poster_url": poster_url,
                        "genres": genres if isinstance(genres, list) else [],
                        "studios": studios if isinstance(studios, list) else [],
                        "mal_id": mal_id,
                        "data_source": "kodik",
                    },
                )

                if kodik_data.get("id"):
                    anime.kodik_id = kodik_data.get("id")
                if kodik_data.get("link"):
                    anime.kodik_link = kodik_data.get("link")
                anime.save(update_fields=["kodik_id", "kodik_link"])

            return {
                "shikimori_id": shikimori_id,
                "title": title_ru or title_en,
                "created": created,
            }

        except Exception as e:
            self.stderr.write(
                f"Error importing anime {kodik_data.get('shikimori_id')}: {e}"
            )
            return None

    def map_status(self, kodik_status):
        """Map Kodik status to our system."""
        status_map = {
            "ongoing": "ongoing",
            "released": "finished",
            "anons": "announced",
            "canceled": "canceled",
        }
        return status_map.get(kodik_status, "finished")

    def map_kind(self, kodik_kind):
        """Map Kodik kind."""
        kind_map = {
            "tv": "tv",
            "tv_13": "tv",
            "tv_24": "tv",
            "tv_48": "tv",
            "movie": "movie",
            "ova": "ova",
            "ona": "ona",
            "special": "special",
            "music": "music",
        }
        return kind_map.get(kodik_kind, "tv")
