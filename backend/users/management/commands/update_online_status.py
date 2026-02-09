from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from datetime import timedelta


class Command(BaseCommand):
    help = 'Update online status for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            help='Actually save to database',
        )

    def handle(self, *args, **options):
        """Обновление статуса онлайн для всех пользователей"""
        cutoff_time = timezone.now() - timedelta(minutes=5)

        if options['save']:
            # Обновляем is_online на основе last_seen
            users_to_update = User.objects.filter(
                last_seen__gte=cutoff_time,
                is_online=False
            )
            count = users_to_update.update(is_online=True)
            self.stdout.write(f'Set online: {count} users')

            # Обновляем оффлайн
            offline_users = User.objects.filter(
                last_seen__lt=cutoff_time,
                is_online=True
            )
            count = offline_users.update(is_online=False)
            self.stdout.write(f'Set offline: {count} users')
        else:
            # Просто выводим статистику без сохранения
            online_count = User.objects.filter(
                last_seen__gte=cutoff_time
            ).count()
            self.stdout.write(f'Users online (by last_seen): {online_count}')