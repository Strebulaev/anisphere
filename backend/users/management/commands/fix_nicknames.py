from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Исправляет никнеймы: для всех пользователей без nickname устанавливает nickname = username. Также делает kaiden812 staff.'

    def handle(self, *args, **options):
        # 1. Исправляем пользователей без никнейма
        fixed = 0
        for user in User.objects.filter(nickname__isnull=True) | User.objects.filter(nickname=''):
            user.nickname = user.username
            if not user.display_name:
                user.display_name = user.username
            user.save(update_fields=['nickname', 'display_name'])
            fixed += 1
            self.stdout.write(f'  Fixed: {user.username} -> nickname={user.nickname}')

        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed} users without nickname.'))

        # 2. Делаем kaiden812 staff + superuser
        try:
            admin = User.objects.get(username='kaiden812')
            admin.is_staff = True
            admin.is_superuser = True
            if not admin.nickname:
                admin.nickname = 'kaiden812'
            if not admin.display_name:
                admin.display_name = 'kaiden812'
            admin.save(update_fields=['is_staff', 'is_superuser', 'nickname', 'display_name'])
            self.stdout.write(self.style.SUCCESS(f'kaiden812 is now staff/superuser. nickname={admin.nickname}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('User kaiden812 not found — will be admin when created.'))

        self.stdout.write(self.style.SUCCESS('Done!'))
