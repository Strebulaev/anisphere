# Generated manually to add missing media_type column
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0012_achievement_attachment_chatinvite_emaillog_favorite_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='postmedia',
            name='media_type',
            field=models.CharField(choices=[('image', 'Изображение'), ('video', 'Видео')], default='image', max_length=20),
        ),
    ]
