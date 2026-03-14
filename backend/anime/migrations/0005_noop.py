from django.db import migrations


class Migration(migrations.Migration):
    """
    Noop миграция для разрешения конфликта
    """

    dependencies = [
        ('anime', '0004_anime_trailer_url'),
    ]

    operations = []
