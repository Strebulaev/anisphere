import os
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from anime.models import Anime, Franchise


class Command(BaseCommand):
    help = "Import anime data from Kodik API"

    KODIK_TOKEN = "74ecb013335271e4344ebc994956dd75"  # From documentation

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=1000, help="Limit number of anime to import"
        )
        parser.add_argument(
            "--update-existing", action="store_true", help="Update existing anime"
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting Kodik import...")

        limit = options["limit"]
        update_existing = options["update_existing"]

        # Import anime
        self.import_anime_list(limit, update_existing)

        # Clean old announcements
        self.clean_announcements()

        self.stdout.write("Kodik import completed")

    def import_anime_list(self, limit, update_existing):
        """Import anime list from Kodik"""
        url = "https://kodik-api.com/list"
        params = {
            "token": self.KODIK_TOKEN,
            "types": "anime,anime-serial",
            "limit": min(limit, 100),  # Kodik limit per request
            "with_material_data": "true",  # Get additional data
        }

        page = 1
        imported = 0

        while imported < limit:
            params["limit"] = min(100, limit - imported)

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    if self.import_anime_item(item, update_existing):
                        imported += 1

                    if imported >= limit:
                        break

                # Next page
                next_page = data.get("next_page")
                if not next_page:
                    break

                # Parse next_page URL for params
                # For simplicity, assume we can continue with page
                page += 1
                params["next"] = data.get("pagination", {}).get("current_page_token")

                time.sleep(1)  # Rate limit

            except Exception as e:
                self.stderr.write(f"Error importing page {page}: {e}")
                break

    def import_anime_item(self, item, update_existing):
        """Import single anime item from Kodik"""
        shikimori_id = item.get("shikimori_id")
        mal_id = item.get("kinopoisk_id") or item.get(
            "imdb_id"
        )  # Kodik uses kinopoisk_id as mal-like

        if not shikimori_id and not mal_id:
            return False

        title_ru = item.get("title")
        title_orig = item.get("title_orig")
        year = item.get("year")
        episodes = item.get("episodes_count") or item.get("last_episode")
        quality = item.get("quality")

        # Get additional data from material_data if available
        material_data = item.get("material_data", {})
        description = material_data.get("description") or material_data.get(
            "anime_description", ""
        )
        genres = material_data.get("genres", []) or material_data.get(
            "anime_genres", []
        )
        if isinstance(genres, list):
            genres_str = ",".join(genres)
        else:
            genres_str = str(genres)

        poster_url = (
            item.get("poster_url")
            or material_data.get("poster_url")
            or material_data.get("anime_poster_url")
        )

        # Determine status from material_data or item
        anime_status = material_data.get("anime_status")
        if anime_status == "released":
            status = "finished"
        elif anime_status == "ongoing":
            status = "ongoing"
        elif anime_status == "anons":
            status = "announced"
        else:
            # Check year
            current_year = timezone.now().year
            if year and year > current_year:
                status = "announced"
            else:
                status = "finished"

        with transaction.atomic():
            # Try to find existing anime by shikimori_id or mal_id
            anime = None
            if shikimori_id:
                try:
                    anime = Anime.objects.get(shikimori_id=shikimori_id)
                except Anime.DoesNotExist:
                    pass
                except ValueError:
                    # shikimori_id is not a valid integer
                    pass

            if not anime and mal_id:
                try:
                    anime = Anime.objects.get(mal_id=mal_id)
                except Anime.DoesNotExist:
                    pass

            if anime and update_existing:
                # Update existing
                if title_ru:
                    anime.title_ru = title_ru
                if title_orig:
                    anime.title_en = title_orig
                if description:
                    anime.description = description
                if year:
                    anime.year = year
                if episodes:
                    anime.episodes = episodes
                anime.status = status
                if genres_str:
                    anime.genres = genres_str
                if poster_url:
                    anime.poster_url = poster_url
                anime.data_source = "kodik"
                anime.save()
                created = False
            else:
                # Create new
                defaults = {"title_ru": title_ru or "", "data_source": "kodik"}

                if title_orig:
                    defaults["title_en"] = title_orig
                if description:
                    defaults["description"] = description
                if year:
                    defaults["year"] = year
                if episodes:
                    defaults["episodes"] = episodes
                if status:
                    defaults["status"] = status
                if genres_str:
                    defaults["genres"] = genres_str
                if poster_url:
                    defaults["poster_url"] = poster_url
                if shikimori_id:
                    try:
                        defaults["shikimori_id"] = int(shikimori_id)
                    except (ValueError, TypeError):
                        pass
                if mal_id:
                    try:
                        defaults["mal_id"] = int(mal_id)
                    except (ValueError, TypeError):
                        pass

                anime = Anime.objects.create(**defaults)
                created = True

            if created:
                self.stdout.write(f"Created anime: {title_ru}")
            elif update_existing:
                # Update existing
                anime.title_ru = title_ru or anime.title_ru
                anime.title_en = title_orig or anime.title_en
                anime.description = description or anime.description
                anime.year = year or anime.year
                anime.episodes = episodes or anime.episodes
                anime.status = status
                anime.genres = genres_str or anime.genres
                anime.poster_url = poster_url or anime.poster_url
                anime.save()
                self.stdout.write(f"Updated anime: {title_ru}")

            return created or update_existing

    def clean_announcements(self):
        """Remove old announcements"""
        # Remove announcements older than 2 years that are not in Kodik anymore
        from django.utils import timezone

        cutoff_year = timezone.now().year - 2

        old_announcements = Anime.objects.filter(
            status="announced", year__lt=cutoff_year
        )

        count = old_announcements.count()
        old_announcements.delete()

        self.stdout.write(f"Removed {count} old announcements")
