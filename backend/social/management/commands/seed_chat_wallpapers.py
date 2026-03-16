"""
Команда для создания предустановленных обоев чатов
"""

from django.core.management.base import BaseCommand
from social.models_chat import ChatWallpaper


class Command(BaseCommand):
    help = 'Создаёт предустановленные обои для чатов'

    def handle(self, *args, **options):
        wallpapers = [
            # Сплошные цвета
            {
                'wallpaper_type': 'solid',
                'wallpaper_color': '#1a1a2e',
                'wallpaper_intensity': 100,
                'preset_name': 'Тёмно-синий',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'solid',
                'wallpaper_color': '#0f0f0f',
                'wallpaper_intensity': 100,
                'preset_name': 'Чёрный',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'solid',
                'wallpaper_color': '#1e3a5f',
                'wallpaper_intensity': 100,
                'preset_name': 'Тёмно-синий 2',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'solid',
                'wallpaper_color': '#2d2d2d',
                'wallpaper_intensity': 100,
                'preset_name': 'Серый',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'solid',
                'wallpaper_color': '#1a2f1a',
                'wallpaper_intensity': 100,
                'preset_name': 'Тёмно-зелёный',
                'is_preset': True,
            },
            
            # Градиенты
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#1a1a2e',
                'wallpaper_color2': '#16213e',
                'wallpaper_intensity': 100,
                'preset_name': 'Ночной градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#0f0c29',
                'wallpaper_color2': '#302b63',
                'wallpaper_intensity': 100,
                'preset_name': 'Фиолетовый градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#232526',
                'wallpaper_color2': '#414345',
                'wallpaper_intensity': 100,
                'preset_name': 'Серый градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#1e3c72',
                'wallpaper_color2': '#2a5298',
                'wallpaper_intensity': 100,
                'preset_name': 'Синий градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#134e5e',
                'wallpaper_color2': '#71b280',
                'wallpaper_intensity': 100,
                'preset_name': 'Изумрудный градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#373B44',
                'wallpaper_color2': '#4286f4',
                'wallpaper_intensity': 100,
                'preset_name': 'Стальной градиент',
                'is_preset': True,
            },
            {
                'wallpaper_type': 'gradient',
                'wallpaper_color': '#0f2027',
                'wallpaper_color2': '#203a43',
                'wallpaper_intensity': 100,
                'preset_name': 'Глубокий градиент',
                'is_preset': True,
            },
        ]

        created_count = 0
        for wallpaper_data in wallpapers:
            wallpaper, created = ChatWallpaper.objects.get_or_create(
                preset_name=wallpaper_data['preset_name'],
                is_preset=True,
                defaults=wallpaper_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Создан пресет: {wallpaper_data["preset_name"]}'))
            else:
                self.stdout.write(f'Пресет уже существует: {wallpaper_data["preset_name"]}')

        self.stdout.write(self.style.SUCCESS(f'\nСоздано {created_count} новых пресетов обоев'))
