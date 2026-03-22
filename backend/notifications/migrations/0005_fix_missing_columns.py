"""
Миграция-заглушка: поля были добавлены вручную через MySQL ALTER TABLE.
Эта миграция просто фиксирует факт что изменения применены.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_rename_notif_user_deleted_idx_notificatio_user_id_77a454_idx_and_more'),
    ]

    operations = [
        # Поля icon, link, is_important, read_at, expires_at добавлены
        # вручную через MySQL ALTER TABLE (миграция 0003 не применилась к БД).
        # Здесь пустая операция — Django считает миграцию выполненной.
    ]
