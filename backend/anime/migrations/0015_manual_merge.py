from django.db import migrations


class Migration(migrations.Migration):
    """
    Ручная merge-миграция.
    Объединяет все листовые ветки в одну точку.
    НЕ выполняет никаких операций с БД.
    """

    dependencies = [
        # Ветка A: от 0002_add_kodik_fields
        ('anime', '0003_anime_screenshots_alter_translation_anime_customdub'),
        # Ветка B: наша длинная цепочка 0003_anime_search_text → ... → 0014
        ('anime', '0014_userepisodeprogress'),
    ]

    operations = []
