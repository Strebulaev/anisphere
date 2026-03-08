from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0013_franchise_anime_franchise'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserEpisodeProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('episode_number', models.PositiveIntegerField(verbose_name='Номер серии')),
                ('status', models.CharField(
                    choices=[
                        ('not_started', 'Не начато'),
                        ('in_progress', 'В процессе'),
                        ('watched',     'Просмотрено'),
                        ('skipped',     'Пропущено'),
                    ],
                    default='not_started',
                    max_length=20,
                    verbose_name='Статус',
                )),
                ('last_position',      models.PositiveIntegerField(default=0, verbose_name='Позиция (сек)')),
                ('duration',           models.PositiveIntegerField(blank=True, null=True, verbose_name='Длительность (сек)')),
                ('is_manually_marked', models.BooleanField(default=False, verbose_name='Ручная отметка')),
                ('watched_at',         models.DateTimeField(blank=True, null=True, verbose_name='Дата просмотра')),
                ('last_watched',       models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')),
                ('created_at',         models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('anime', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='episode_progress',
                    to='anime.anime',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='episode_progress',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Прогресс серии',
                'verbose_name_plural': 'Прогресс серий',
                'ordering': ['episode_number'],
                'unique_together': {('user', 'anime', 'episode_number')},
            },
        ),
    ]
