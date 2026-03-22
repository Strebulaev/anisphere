from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Создаёт модель ChatTopic.
    Поля franchise_id / discussion_type / folder_type уже были добавлены
    в миграции 0021, поэтому здесь их нет.
    """

    dependencies = [
        ('social', '0022_add_groupchat_members_count'),
        ('anime', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatTopic',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='topics',
                    to='social.groupchat',
                    verbose_name='Чат',
                )),
                ('anime', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='discussion_topics',
                    to='anime.anime',
                    verbose_name='Аниме',
                )),
            ],
            options={
                'verbose_name': 'Тема обсуждения',
                'verbose_name_plural': 'Темы обсуждений',
                'ordering': ['order'],
                'unique_together': {('chat', 'anime')},
            },
        ),
    ]
