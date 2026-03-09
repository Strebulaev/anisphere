from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudioDiscussionReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Содержание')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='studio_discussion_replies',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('discussion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='replies',
                    to='studios.studiodiscussion',
                )),
            ],
            options={
                'verbose_name': 'Ответ на обсуждение',
                'verbose_name_plural': 'Ответы на обсуждения',
                'ordering': ['created_at'],
            },
        ),
    ]
