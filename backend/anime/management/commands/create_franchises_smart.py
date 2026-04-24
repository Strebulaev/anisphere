import os
import sys
import re
import django
from collections import defaultdict
from typing import Optional, Tuple

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.management.base import BaseCommand
from anime.models import Anime, Franchise


class Command(BaseCommand):
    help = "Smart grouping of anime into franchises"

    def handle(self, *args, **options):
        self.stdout.write("Starting smart franchise creation...")

        # Get all anime
        animes = Anime.objects.exclude(title_ru="").order_by("title_ru")
        total_animes = animes.count()
        self.stdout.write(f"Processing {total_animes} anime...")

        # Group by core name
        groups = defaultdict(list)
        processed = set()

        for anime in animes:
            if anime.id in processed:
                continue

            core_name = self.extract_core_name(anime.title_ru)
            if core_name:
                # Find similar anime
                similar = []
                for other in animes:
                    if other.id in processed:
                        continue
                    if self.extract_core_name(other.title_ru) == core_name:
                        similar.append(other)
                        processed.add(other.id)

                if len(similar) > 1:
                    groups[core_name] = similar
                else:
                    processed.add(anime.id)

        # Create franchises
        created_count = 0
        for core_name, anime_list in groups.items():
            franchise = self.create_franchise(core_name, anime_list)
            if franchise:
                created_count += 1

        self.stdout.write(f"Created {created_count} franchises")

    def extract_core_name(self, title: str) -> Optional[str]:
        """Extract core franchise name from anime title"""
        # Remove common suffixes
        title = re.sub(
            r"\s+(?:TV|OVA|ONA|Movie|Special|Part\s*\d+|Season\s*\d+|S\d+|第\d+話).*?$",
            "",
            title,
            flags=re.IGNORECASE,
        )

        # Remove numbers and special chars at end
        title = re.sub(r"[\d\s\-_\.]+$", "", title)

        # Remove common words
        title = re.sub(
            r"\b(?:the|a|an|and|or|of|in|on|at|to|for|with|by|as|is|was|were|be|been|being|have|has|had|do|does|did|will|would|can|could|may|might|must|shall|should)\b",
            "",
            title,
            flags=re.IGNORECASE,
        )

        # Clean up
        title = re.sub(r"\s+", " ", title).strip()

        return title.lower() if len(title) > 2 else None

    def create_franchise(self, core_name: str, anime_list: list) -> Optional[Franchise]:
        """Create franchise from anime list"""
        try:
            # Check if franchise already exists
            existing = Franchise.objects.filter(name__iexact=core_name).first()
            if existing:
                self.stdout.write(f'Franchise "{core_name}" already exists')
                return None

            # Create franchise
            franchise = Franchise.objects.create(
                name=core_name,
                description=f"Франшиза: {core_name}",
                poster_url=anime_list[0].poster_url
                if anime_list[0].poster_url
                else None,
            )

            # Set order for anime
            for i, anime in enumerate(sorted(anime_list, key=lambda x: x.year or 9999)):
                anime.franchise = franchise
                anime.franchise_order = i + 1
                anime.save(update_fields=["franchise", "franchise_order"])

            franchise.update_aggregated_data()
            self.stdout.write(
                f'Created franchise "{core_name}" with {len(anime_list)} anime'
            )
            return franchise

        except Exception as e:
            self.stderr.write(f'Error creating franchise "{core_name}": {e}')
            return None
