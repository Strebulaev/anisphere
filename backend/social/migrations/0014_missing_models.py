"""
Migration: добавляет модели которые есть в models_chat.py но не были смигрированы:
- PrivateChatSettings
- GroupMemberSettings
- ChatTopic
- UserGlobalChatStyle
- franchise_id / discussion_type / folder_type поля в GroupChat (если ещё нет)
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0013_chat_settings_full'),
        ('anime', '0001_initial'),
    ]

    operations = [

        # ── GroupChat: franchise_id, discussion_type, folder_type ──
        # Добавляем только если полей ещё нет (используем SeparateDatabaseAndState при необходимости)
        migrations.AddField(
            model_name='groupchat',
            name='franchise_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, verbose_name='ИД франшизы'),
            preserve_default=True,
        ) if False else migrations.RunSQL('SELECT 1'),  # placeholder — заменяется ниже

        # Настоящие операции:
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- franchise_id
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='social_groupchat' AND column_name='franchise_id'
                ) THEN
                    ALTER TABLE social_groupchat ADD COLUMN franchise_id integer NULL;
                    CREATE INDEX IF NOT EXISTS social_groupchat_franchise_id_idx ON social_groupchat(franchise_id);
                END IF;

                -- discussion_type
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='social_groupchat' AND column_name='discussion_type'
                ) THEN
                    ALTER TABLE social_groupchat ADD COLUMN discussion_type varchar(30) NOT NULL DEFAULT '';
                END IF;

                -- folder_type
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='social_groupchat' AND column_name='folder_type'
                ) THEN
                    ALTER TABLE social_groupchat ADD COLUMN folder_type varchar(30) NOT NULL DEFAULT 'groups';
                END IF;
            END
            $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ── PrivateChatSettings ──
        migrations.CreateModel(
            name='PrivateChatSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_name', models.CharField(blank=True, max_length=255)),
                ('custom_avatar', models.ImageField(blank=True, null=True, upload_to='private_chat_avatars/')),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('sound_enabled', models.BooleanField(default=True)),
                ('notification_sound', models.CharField(default='default', max_length=50)),
                ('vibration_enabled', models.BooleanField(default=True)),
                ('vibration_type', models.CharField(default='default', max_length=20)),
                ('show_preview', models.BooleanField(default=True)),
                ('show_popup', models.BooleanField(default=True)),
                ('muted_until', models.DateTimeField(blank=True, null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('is_pinned', models.BooleanField(default=False)),
                ('is_hidden', models.BooleanField(default=False)),
                ('is_blocked', models.BooleanField(default=False)),
                ('blocked_at', models.DateTimeField(blank=True, null=True)),
                ('auto_delete_enabled', models.BooleanField(default=False)),
                ('auto_delete_after', models.IntegerField(blank=True, null=True)),
                ('folder_id', models.IntegerField(blank=True, null=True)),
                ('tags', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='settings',
                    to='social.privatechat',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='private_chat_settings_v2',
                    to='users.user',
                )),
            ],
            options={
                'verbose_name': 'Настройки личного чата',
                'verbose_name_plural': 'Настройки личных чатов',
            },
        ),
        migrations.AlterUniqueTogether(
            name='privatechatsettings',
            unique_together={('chat', 'user')},
        ),
        migrations.AddIndex(
            model_name='privatechatsettings',
            index=models.Index(fields=['user', 'is_pinned'], name='prvchat_set_user_pin_idx'),
        ),
        migrations.AddIndex(
            model_name='privatechatsettings',
            index=models.Index(fields=['user', 'is_archived'], name='prvchat_set_user_arc_idx'),
        ),

        # ── GroupMemberSettings ──
        migrations.CreateModel(
            name='GroupMemberSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('mentions_only', models.BooleanField(default=False)),
                ('sound_enabled', models.BooleanField(default=True)),
                ('show_preview', models.BooleanField(default=True)),
                ('muted_until', models.DateTimeField(blank=True, null=True)),
                ('is_pinned', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False)),
                ('tags', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('membership', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='personal_settings',
                    to='social.chatmember',
                )),
            ],
            options={
                'verbose_name': 'Настройки участника группы',
                'verbose_name_plural': 'Настройки участников групп',
            },
        ),

        # ── ChatTopic ──
        migrations.CreateModel(
            name='ChatTopic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
            },
        ),
        migrations.AlterUniqueTogether(
            name='chattopic',
            unique_together={('chat', 'anime')},
        ),

        # ── UserGlobalChatStyle ──
        migrations.CreateModel(
            name='UserGlobalChatStyle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallpaper_type', models.CharField(default='solid', max_length=20)),
                ('wallpaper_color', models.CharField(default='#0f0f0f', max_length=7)),
                ('wallpaper_color2', models.CharField(default='#1a1a2e', max_length=7)),
                ('bubble_style', models.CharField(default='modern', max_length=20)),
                ('accent_color', models.CharField(default='#6C5CE7', max_length=7)),
                ('font_size', models.CharField(default='medium', max_length=20)),
                ('message_animation', models.CharField(default='slide', max_length=20)),
                ('emoji_set', models.CharField(default='default', max_length=30)),
                ('time_format', models.CharField(default='24h', max_length=4)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='global_chat_style',
                    to='users.user',
                    verbose_name='Пользователь',
                )),
            ],
            options={
                'verbose_name': 'Глобальные настройки чата',
                'verbose_name_plural': 'Глобальные настройки чатов',
            },
        ),
    ]
