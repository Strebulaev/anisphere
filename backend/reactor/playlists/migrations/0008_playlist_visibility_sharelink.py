from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('playlists', '0007_alter_favoriteanime_options_and_more'),
    ]

    operations = [
        # Добавляем поле visibility
        migrations.AddField(
            model_name='playlist',
            name='visibility',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('public', 'Публичный'),
                    ('private', 'Приватный'),
                    ('link', 'По ссылке'),
                ],
                default='public',
                verbose_name='Видимость',
            ),
        ),
        # Мигрируем is_public → visibility
        migrations.RunSQL(
            sql="""
                UPDATE playlists_playlist
                SET visibility = CASE
                    WHEN is_public = TRUE THEN 'public'
                    ELSE 'private'
                END;
            """,
            reverse_sql="UPDATE playlists_playlist SET is_public = (visibility = 'public');",
        ),
        # Создаём таблицу share-ссылок
        migrations.CreateModel(
            name='PlaylistShareLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='share_links',
                    to='playlists.playlist',
                )),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Истекает')),
                ('is_active', models.BooleanField(default=True)),
                ('access_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Share-ссылка плейлиста',
                'verbose_name_plural': 'Share-ссылки плейлистов',
                'ordering': ['-created_at'],
            },
        ),
    ]
