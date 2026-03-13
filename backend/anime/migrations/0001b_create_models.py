"""
Stub-миграция. Файл был удалён, но запись в django_migrations осталась.
Django требует наличия файла с классом Migration — этот файл её предоставляет.
Не выполняет никаких операций с БД.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0001_initial'),
    ]

    operations = []
