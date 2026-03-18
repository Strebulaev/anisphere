"""
Патч для миграции 0017 — убирает невалидные DEFAULT для MySQL.

ПРИМЕНЕНИЕ НА СЕРВЕРЕ:
1. Скопировать этот файл в social/migrations/fix_0017_time_color.py
2. Выполнить: python manage.py migrate social
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Этот файл НЕ нужен — см. инструкцию ниже.
    Вместо этого отредактируйте 0017_... напрямую.
    """
    dependencies = []
    operations = []
