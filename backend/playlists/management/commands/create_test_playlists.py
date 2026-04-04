from django.core.management.base import BaseCommand
from playlists.models import Playlist, PlaylistItem
from anime.models import Anime
from dubs.models import DubGroup
from users.models import User

class Command(BaseCommand):
    help = 'Создает тестовые плейлисты'

    def handle(self, *args, **options):
        # Получаем тестового пользователя (суперпользователя)
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123'
                )
                self.stdout.write(self.style.SUCCESS(f'Создан тестовый пользователь: {user.username}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Не удалось получить пользователя: {e}'))
            return

        # Получаем аниме
        animes = list(Anime.objects.all()[:3])
        if not animes:
            self.stdout.write(self.style.WARNING('Нет аниме в базе. Сначала запустите fill_test_data'))
            return

        # Получаем группы озвучек
        dub_groups = list(DubGroup.objects.all()[:2])

        # Создаем плейлисты
        playlists_data = [
            {
                'title': 'Мои любимые тайтлы',
                'description': 'Коллекция лучших аниме, которые я посмотрел',
                'is_public': True,
                'items': [
                    {'anime': animes[0], 'source_url': 'https://jut.su/example1/', 'episode_number': 1},
                    {'anime': animes[1], 'source_url': 'https://jut.su/example2/', 'episode_number': 1},
                ]
            },
            {
                'title': 'Для просмотра позже',
                'description': 'Аниме, которые хочу посмотреть',
                'is_public': False,
                'items': [
                    {'anime': animes[2], 'source_url': 'https://animego.org/example/', 'episode_number': None},
                ]
            },
        ]

        for playlist_data in playlists_data:
            items_data = playlist_data.pop('items')

            playlist, created = Playlist.objects.get_or_create(
                user=user,
                title=playlist_data['title'],
                defaults=playlist_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан плейлист: {playlist.title}'))

                # Добавляем элементы
                for item_data in items_data:
                    item, item_created = PlaylistItem.objects.get_or_create(
                        playlist=playlist,
                        anime=item_data['anime'],
                        defaults={
                            'source_url': item_data['source_url'],
                            'episode_number': item_data['episode_number'],
                            'dub_studio': dub_groups[0] if dub_groups and item_data.get('episode_number') else None
                        }
                    )
                    if item_created:
                        self.stdout.write(f'  Добавлен элемент: {item.anime.title_ru}')

        self.stdout.write(self.style.SUCCESS('Тестовые плейлисты созданы!'))