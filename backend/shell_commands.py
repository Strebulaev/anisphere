from anime.models import Anime, Genre, Studio

# Создаем жанры
genres = ['Экшен', 'Приключения', 'Комедия', 'Драма', 'Фэнтези', 'Романтика']
for genre_name in genres:
    genre, created = Genre.objects.get_or_create(name=genre_name)
    print('Genre:', genre.name, '- Created' if created else 'Exists')

# Создаем студии
studios = ['Studio Pierrot', 'WIT Studio', 'MAPPA']
for studio_name in studios:
    studio, created = Studio.objects.get_or_create(name=studio_name)
    print('Studio:', studio.name, '- Created' if created else 'Exists')

# Создаем тестовые аниме
anime_list = [
    {
        'title_ru': 'Наруто',
        'title_en': 'Naruto',
        'title_jp': 'ナルト',
        'description': 'Легендарная история о молодом ниндзя.',
        'poster_url': 'https://shikimori.one/system/animes/original/20.jpeg',
        'year': 2002,
        'status': 'finished',
        'episodes': 720,
        'score': 8.3,
        'data_source': 'shikimori',
        'shikimori_id': '20'
    },
    {
        'title_ru': 'Атака титанов',
        'title_en': 'Attack on Titan',
        'title_jp': '進撃の巨人',
        'description': 'Человечество борется за выживание против гигантских титанов.',
        'poster_url': 'https://shikimori.one/system/animes/original/16498.jpeg',
        'year': 2013,
        'status': 'finished',
        'episodes': 87,
        'score': 9.0,
        'data_source': 'shikimori',
        'shikimori_id': '16498'
    }
]

for anime_data in anime_list:
    anime, created = Anime.objects.get_or_create(
        shikimori_id=anime_data['shikimori_id'],
        defaults=anime_data
    )
    print('Anime:', anime.title_ru, '- Created' if created else 'Exists')

print('Test data creation completed!')
exit()