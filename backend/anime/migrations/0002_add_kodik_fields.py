# Generated migration for adding Kodik fields to Anime model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='anime',
            name='kodik_link',
            field=models.URLField(blank=True, verbose_name='Ссылка на плеер Kodik'),
        ),
        migrations.AddField(
            model_name='anime',
            name='kodik_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='Kodik ID'),
        ),
        migrations.AddField(
            model_name='anime',
            name='quality',
            field=models.CharField(blank=True, max_length=20, verbose_name='Качество видео'),
        ),
        migrations.AddField(
            model_name='anime',
            name='screenshots',
            field=models.JSONField(blank=True, default=list, verbose_name='Скриншоты'),
        ),
        migrations.AddField(
            model_name='anime',
            name='seasons',
            field=models.JSONField(blank=True, default=dict, verbose_name='Сезоны и серии'),
        ),
        migrations.AddField(
            model_name='anime',
            name='last_season',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Последний сезон'),
        ),
        migrations.AddField(
            model_name='anime',
            name='last_episode',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Последняя серия'),
        ),
        migrations.AddField(
            model_name='anime',
            name='translations',
            field=models.JSONField(blank=True, default=list, verbose_name='Переводы'),
        ),
    ]
