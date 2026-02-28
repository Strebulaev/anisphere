from django.core.management.base import BaseCommand
from anime.models import Anime, Genre

class Command(BaseCommand):
    help = 'Test import with demo data (no internet required)'

    def handle(self, *args, **options):
        self.stdout.write('Testing import with demo data...')
        self.stdout.write('=' * 50)
        
        # Demo data
        demo_anime = {
            'title_ru': 'Тест Аниме',
            'title_en': 'Test Anime',
            'description': 'Demo description for testing',
            'year': 2026,
            'status': 'ongoing',
            'episodes': 12,
            'score': 8.5,
            'poster_url': 'https://example.com/poster.jpg',
            'genres': ['Экшен', 'Приключения', 'Драма']
        }
        
        try:
            # Create genres first
            genre_objects = []
            for genre_name in demo_anime['genres']:
                genre, created = Genre.objects.get_or_create(
                    name=genre_name,
                    defaults={'slug': genre_name.lower().replace(' ', '-')}
                )
                genre_objects.append(genre)
            
            # Create anime
            anime = Anime.objects.create(
                title_ru=demo_anime['title_ru'],
                title_en=demo_anime['title_en'],
                description=demo_anime['description'],
                year=demo_anime['year'],
                status=demo_anime['status'],
                episodes=demo_anime['episodes'],
                score=demo_anime['score'],
                poster_url=demo_anime['poster_url'],
                data_source='demo'
            )
            
            # Set genres after save (this was the original issue)
            anime.genres.set(genre_objects)
            
            self.stdout.write(self.style.SUCCESS(f'Success! Anime created: {anime.title_ru}'))
            self.stdout.write(f'Genres: {", ".join([g.name for g in anime.genres.all()])}')
            
            # Test querying
            all_anime = Anime.objects.all()
            self.stdout.write(f'Total anime in database: {all_anime.count()}')
            
            self.stdout.write(self.style.SUCCESS('Demo test completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()