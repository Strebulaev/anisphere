from django.core.management.base import BaseCommand
from anime.models import Anime, Genre

class Command(BaseCommand):
    help = 'Add demo anime for testing the player'

    def handle(self, *args, **options):
        self.stdout.write('Adding demo anime for testing...')
        
        # Создаем демо-жанры
        action_genre, _ = Genre.objects.get_or_create(
            name='Экшен',
            defaults={'slug': 'ekshen'}
        )
        
        drama_genre, _ = Genre.objects.get_or_create(
            name='Драма', 
            defaults={'slug': 'drama'}
        )
        
        comedy_genre, _ = Genre.objects.get_or_create(
            name='Комедия',
            defaults={'slug': 'komediya'}
        )
        
        # Создаем демо-аниме
        demo_anime = [
            {
                'title_ru': 'Демо Аниме 1',
                'title_en': 'Demo Anime 1',
                'description': 'Это демо-аниме для тестирования системы просмотра.',
                'year': 2024,
                'status': 'finished',
                'episodes': 12,
                'score': 8.5,
                'poster_url': 'https://via.placeholder.com/300x400/3b82f6/ffffff?text=Demo+Anime+1',
                'genres': [action_genre, drama_genre],
                'shikimori_id': 12345  # Тестовый ID
            },
            {
                'title_ru': 'Демо Аниме 2',
                'title_en': 'Demo Anime 2', 
                'description': 'Второе демо-аниме для проверки функциональности.',
                'year': 2023,
                'status': 'ongoing',
                'episodes': 8,
                'score': 7.8,
                'poster_url': 'https://via.placeholder.com/300x400/ef4444/ffffff?text=Demo+Anime+2',
                'genres': [comedy_genre, drama_genre],
                'shikimori_id': 12346  # Тестовый ID
            }
        ]
        
        for anime_data in demo_anime:
            # Создаем аниме без жанров сначала
            anime_create_data = anime_data.copy()
            genres = anime_create_data.pop('genres')
            
            anime, created = Anime.objects.get_or_create(
                title_ru=anime_data['title_ru'],
                defaults=anime_create_data
            )
            
            if created:
                # Устанавливаем жанры после создания
                anime.genres.set(genres)
                self.stdout.write(self.style.SUCCESS(f'Created: {anime.title_ru}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {anime.title_ru}'))
        
        # Показываем статистику
        total_anime = Anime.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total anime in database: {total_anime}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo anime added! You can now test the player.'))