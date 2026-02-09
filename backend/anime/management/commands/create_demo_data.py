from django.core.management.base import BaseCommand
from anime.models import Anime, Genre
import random

class Command(BaseCommand):
    help = 'Создание демо-данных аниме для тестирования'

    def handle(self, *args, **options):
        self.stdout.write('Создание демо-данных аниме...')
        
        # Создаем жанры если их нет
        genres_data = [
            ('Экшен', 'action'),
            ('Приключения', 'adventure'),
            ('Комедия', 'comedy'),
            ('Драма', 'drama'),
            ('Фантастика', 'fantasy'),
            ('Романтика', 'romance'),
            ('Триллер', 'thriller'),
            ('Ужасы', 'horror'),
            ('Спорт', 'sport'),
            ('Школа', 'school')
        ]
        
        created_genres = []
        for name, slug in genres_data:
            try:
                genre, created = Genre.objects.get_or_create(
                    name=name,
                    defaults={'slug': slug}
                )
                created_genres.append(genre)
                if created:
                    self.stdout.write(f'Создан жанр: {name}')
                else:
                    self.stdout.write(f'Жанр уже существует: {name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка создания жанра {name}: {e}'))
        
        # Создаем демо-аниме
        demo_anime = [
            {
                'title_ru': 'Наруто',
                'title_en': 'Naruto',
                'title_jp': 'ナルト',
                'description': 'История о молодом ниндзя, который мечтает стать Хокаге.',
                'year': 2002,
                'status': 'finished',
                'episodes': 220,
                'score': 8.3,
                'poster_url': 'https://via.placeholder.com/300x450/FF6B6B/FFFFFF?text=Naruto',
                'genres': ['Экшен', 'Приключения', 'Комедия']
            },
            {
                'title_ru': 'Атака Титанов',
                'title_en': 'Attack on Titan',
                'title_jp': '進撃の巨人',
                'description': 'В мире, где человечество живет в городах, окруженных гигантскими стенами.',
                'year': 2013,
                'status': 'finished',
                'episodes': 87,
                'score': 9.0,
                'poster_url': 'https://via.placeholder.com/300x450/4ECDC4/FFFFFF?text=AOT',
                'genres': ['Экшен', 'Драма', 'Фантастика']
            },
            {
                'title_ru': 'Моя геройская академия',
                'title_en': 'My Hero Academia',
                'title_jp': '僕のヒーローアカデミア',
                'description': 'В мире, где почти у всех людей есть суперсилы.',
                'year': 2016,
                'status': 'ongoing',
                'episodes': 138,
                'score': 8.5,
                'poster_url': 'https://via.placeholder.com/300x450/45B7D1/FFFFFF?text=MHA',
                'genres': ['Экшен', 'Комедия', 'Школа']
            },
            {
                'title_ru': 'Джujutsu Kaisen',
                'title_en': 'Jujutsu Kaisen',
                'title_jp': '呪術廻戦',
                'description': 'Ученик становится приемником проклятого духа.',
                'year': 2020,
                'status': 'ongoing',
                'episodes': 24,
                'score': 8.7,
                'poster_url': 'https://via.placeholder.com/300x450/96CEB4/FFFFFF?text=JJK',
                'genres': ['Экшен', 'Фантастика', 'Ужасы']
            },
            {
                'title_ru': 'Демон-убийца',
                'title_en': 'Demon Slayer',
                'title_jp': '鬼滅の刃',
                'description': 'Мальчик становится убийцей демонов, чтобы спасти свою сестру.',
                'year': 2019,
                'status': 'finished',
                'episodes': 44,
                'score': 8.6,
                'poster_url': 'https://via.placeholder.com/300x450/FFEAA7/000000?text=DS',
                'genres': ['Экшен', 'Фантастика', 'Приключения']
            }
        ]
        
        for anime_data in demo_anime:
            # Получаем жанры
            anime_genres = []
            for genre_name in anime_data['genres']:
                genre = next((g for g in created_genres if g.name == genre_name), None)
                if genre:
                    anime_genres.append(genre)
            
            # Создаем аниме
            anime, created = Anime.objects.get_or_create(
                title_ru=anime_data['title_ru'],
                defaults={
                    'title_en': anime_data['title_en'],
                    'title_jp': anime_data['title_jp'],
                    'description': anime_data['description'],
                    'year': anime_data['year'],
                    'status': anime_data['status'],
                    'episodes': anime_data['episodes'],
                    'score': anime_data['score'],
                    'poster_url': anime_data['poster_url'],
                    'data_source': 'demo'
                }
            )
            
            if created:
                # Устанавливаем жанры
                anime.genres.set(anime_genres)
                self.stdout.write(self.style.SUCCESS(f'Создано аниме: {anime.title_ru}'))
            else:
                self.stdout.write(self.style.WARNING(f'Аниме уже существует: {anime.title_ru}'))
        
        # Показываем статистику
        total_anime = Anime.objects.count()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Демо-данные созданы!'))
        self.stdout.write(f'Всего аниме в базе: {total_anime}')
        
        # Показываем список аниме
        self.stdout.write('')
        self.stdout.write('Список аниме:')
        for anime in Anime.objects.all():
            self.stdout.write(f'  • {anime.title_ru} ({anime.year}) - {anime.status}')