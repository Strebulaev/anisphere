# Generated migration for announcement fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0015_manual_merge'),
    ]

    operations = [
        # Add 'released' to STATUS_CHOICES
        migrations.AlterField(
            model_name='anime',
            name='status',
            field=models.CharField(
                choices=[
                    ('ongoing', 'Онгоинг'),
                    ('finished', 'Завершен'),
                    ('announced', 'Анонсирован'),
                    ('released', 'Вышел'),
                    ('canceled', 'Отменен'),
                ],
                default='finished',
                max_length=20,
                verbose_name='Статус'
            ),
        ),
        
        # Add mal_id field
        migrations.AddField(
            model_name='anime',
            name='mal_id',
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name='MAL ID'
            ),
        ),
        
        # Add release_date field
        migrations.AddField(
            model_name='anime',
            name='release_date',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Дата выхода'
            ),
        ),
        
        # Add release_date_string field
        migrations.AddField(
            model_name='anime',
            name='release_date_string',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Дата выхода (строка)'
            ),
        ),
    ]
