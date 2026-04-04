# Migration for is_public field (favorites tables already exist)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playlists', '0003_favorites_and_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]


    
