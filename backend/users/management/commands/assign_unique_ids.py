from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Присваивает уникальный ID всем пользователям, у которых его нет'

    def handle(self, *args, **options):
        users_without_id = User.objects.filter(unique_id__isnull=True) | User.objects.filter(unique_id='')
        count = users_without_id.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Все пользователи уже имеют unique_id'))
            return

        self.stdout.write(f'Найдено {count} пользователей без unique_id')

        for user in users_without_id:
            user.ensure_unique_id()
            self.stdout.write(f'  Присвоен ID {user.unique_id} пользователю {user.username}')

        self.stdout.write(self.style.SUCCESS(f'Успешно присвоено {count} уникальных ID'))
