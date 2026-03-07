# Generated manually 2026-03-06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0012_anime_genres_anime_studios'),
    ]

    operations = [
        migrations.CreateModel(
            name='Franchise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('slug', models.SlugField(blank=True, max_length=255, verbose_name='Слаг')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('poster_url', models.URLField(blank=True, verbose_name='URL постера')),
                ('poster', models.ImageField(blank=True, null=True, upload_to='franchise_posters/')),
                ('score', models.FloatField(blank=True, null=True, verbose_name='Рейтинг (усредн.)')),
                ('year_start', models.PositiveIntegerField(blank=True, null=True, verbose_name='Год начала')),
                ('year_end', models.PositiveIntegerField(blank=True, null=True, verbose_name='Год конца')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Франшиза',
                'verbose_name_plural': 'Франшизы',
                'ordering': ['-score'],
            },
        ),
        migrations.AddField(
            model_name='anime',
            name='franchise',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='entries',
                to='anime.franchise',
                verbose_name='Франшиза',
            ),
        ),
        migrations.AddField(
            model_name='anime',
            name='franchise_order',
            field=models.PositiveIntegerField(default=0, verbose_name='Порядок во франшизе'),
        ),
    ]
