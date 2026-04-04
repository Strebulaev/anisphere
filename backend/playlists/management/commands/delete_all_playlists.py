from django.core.management.base import BaseCommand
from playlists.models import Playlist, PlaylistItem, FavoritePlaylist


class Command(BaseCommand):
    help = 'Удаляет все плейлисты и связанные данные'

    def handle(self, *args, **options):
        # Удаляем все избранные плейлисты
        favorite_count = FavoritePlaylist.objects.count()
        FavoritePlaylist.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Удалено {favorite_count} избранных плейлистов'))

        # Удаляем все элементы плейлистов
        items_count = PlaylistItem.objects.count()
        PlaylistItem.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Удалено {items_count} элементов плейлистов'))

        # Удаляем все плейлисты
        playlists_count = Playlist.objects.count()
        Playlist.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено {playlists_count} плейлистов'))

        self.stdout.write(self.style.SUCCESS('Все плейлисты успешно удалены!'))
