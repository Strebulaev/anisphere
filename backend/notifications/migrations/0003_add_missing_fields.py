from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_alter_notification_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('anime', '0014_userepisodeprogress'),
    ]

    operations = [
        # Добавляем недостающие поля Notification
        migrations.AddField(
            model_name='notification',
            name='icon',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='notification',
            name='is_important',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='notification',
            name='read_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Обновляем choices для типа уведомления (полный список)
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('like', 'Лайк'),
                    ('dislike', 'Дизлайк'),
                    ('heart', 'Сердечко'),
                    ('comment', 'Комментарий'),
                    ('reply', 'Ответ на комментарий'),
                    ('mention', 'Упоминание'),
                    ('follow', 'Подписка'),
                    ('repost', 'Репост'),
                    ('message', 'Сообщение'),
                    ('group_message', 'Сообщение в группе'),
                    ('group_invite', 'Приглашение в группу'),
                    ('achievement', 'Достижение'),
                    ('contest', 'Новый конкурс'),
                    ('contest_vote', 'Голосование'),
                    ('contest_results', 'Результаты конкурса'),
                    ('contest_win', 'Победа в конкурсе'),
                    ('reminder_episode', 'Напоминание о серии'),
                    ('reminder_event', 'Напоминание о событии'),
                    ('reminder_contest', 'Напоминание о конкурсе'),
                    ('system', 'Системное'),
                    ('warning', 'Предупреждение'),
                    ('security', 'Безопасность'),
                ],
            ),
        ),
        # Добавляем индекс по is_deleted
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_deleted', 'created_at'], name='notif_user_deleted_idx'),
        ),
        # Создаём модель Reminder
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_time', models.DateTimeField(verbose_name='Время напоминания')),
                ('repeat_weekly', models.BooleanField(default=False, verbose_name='Повторять еженедельно')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('is_triggered', models.BooleanField(default=False, verbose_name='Сработало')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('anime', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to='anime.anime',
                )),
            ],
            options={
                'verbose_name': 'Напоминание',
                'verbose_name_plural': 'Напоминания',
                'ordering': ['-reminder_time'],
                'indexes': [
                    models.Index(fields=['user', 'is_active'], name='reminder_user_active_idx'),
                    models.Index(fields=['reminder_time', 'is_active'], name='reminder_time_active_idx'),
                ],
                'unique_together': {('user', 'anime', 'reminder_time')},
            },
        ),
        # Создаём модель NotificationSetting
        migrations.CreateModel(
            name='NotificationSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_settings', models.JSONField(default=dict)),
                ('push_enabled', models.BooleanField(default=True)),
                ('email_enabled', models.BooleanField(default=True)),
                ('sound_enabled', models.BooleanField(default=True)),
                ('dnd_enabled', models.BooleanField(default=False)),
                ('dnd_start', models.TimeField(blank=True, null=True)),
                ('dnd_end', models.TimeField(blank=True, null=True)),
                ('auto_clean_read_days', models.IntegerField(default=30)),
                ('auto_clean_unread_days', models.IntegerField(default=90)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notif_settings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Настройки уведомлений',
            },
        ),
    ]
