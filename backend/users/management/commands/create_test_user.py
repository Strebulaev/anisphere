from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User, UserSettings


class Command(BaseCommand):
    help = 'Create test user with settings'

    def handle(self, *args, **options):
        # Создаем тестового пользователя если не существует
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'password': make_password('testpass123'),
                'first_name': 'Test',
                'last_name': 'User',
                'display_name': 'Тестовый Пользователь',
                'nickname': 'testuser_nick'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created test user'))
            # Создаем настройки для пользователя
            UserSettings.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS('Created user settings'))
        else:
            self.stdout.write(self.style.WARNING('Test user already exists'))

        self.stdout.write(f'User: {user.username}, has settings: {hasattr(user, "settings")}')
        if hasattr(user, 'settings'):
            settings = user.settings
            self.stdout.write(f'Settings: theme={settings.theme}, notifications={settings.email_notifications}')