from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge-миграция: объединяет две ветки 0005_*.
    """

    dependencies = [
        ('anime', '0005_anime_screenshots'),
        ('anime', '0005_noop'),
    ]

    operations = []
