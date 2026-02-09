import os
import django
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime, Genre
from django.db.models import Count

print('=== Genres ===')
genres = Genre.objects.all()
for g in genres:
    print(f"  {g.id}: {g.name}")

print('\n=== Anime Statuses ===')
statuses = Anime.objects.values('status').annotate(count=Count('id'))
for s in statuses:
    print(f"  {s['status']}: {s['count']}")

print('\n=== Sample Anime ===')
anime = Anime.objects.first()
if anime:
    print(f"  Title: {anime.title_ru}")
    print(f"  Status: {anime.status}")
    print(f"  Year: {anime.year}")
    print(f"  Genres: {anime.genres}")
    print(f"  Score: {anime.score}")

print('\n=== Years Range ===')
min_year = Anime.objects.aggregate(min_year=Count('year'))
years = Anime.objects.values('year').distinct().order_by('year')
print(f"  Min year: {years.first()['year'] if years else 'N/A'}")
print(f"  Max year: {years.last()['year'] if years else 'N/A'}")
