from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0012_achievement_attachment_chatinvite_emaillog_favorite_and_more'),
        migrations.swappable_dependency('users.User'),
    ]

    operations = [
        # ── ChatInviteLink ──
        migrations.CreateModel(
            name='ChatInviteLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100)),
                ('invite_link', models.CharField(max_length=100, unique=True)),
                ('link_type', models.CharField(
                    choices=[('primary','Основная'),('temporary','Временная'),('personal','Персональная')],
                    default='temporary', max_length=20
                )),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('usage_limit', models.IntegerField(blank=True, null=True)),
                ('usage_count', models.IntegerField(default=0)),
                ('is_revoked', models.BooleanField(default=False)),
                ('is_primary', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invite_links', to='social.groupchat')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_invite_links', to='users.user')),
                ('auto_assign_role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invite_links', to='social.chatrole')),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='personal_invite_links', to='users.user')),
            ],
            options={'verbose_name': 'Ссылка-приглашение', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='chatinvitelink',
            index=models.Index(fields=['invite_link'], name='social_chatinvitelink_invite_link_idx'),
        ),
        migrations.AddIndex(
            model_name='chatinvitelink',
            index=models.Index(fields=['chat', 'is_revoked'], name='social_chatinvitelink_chat_revoked_idx'),
        ),

        # ── ChatWallpaper ──
        migrations.CreateModel(
            name='ChatWallpaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallpaper_type', models.CharField(
                    choices=[('solid','Сплошной цвет'),('gradient','Градиент'),('pattern','Паттерн'),('image','Изображение')],
                    default='solid', max_length=20
                )),
                ('wallpaper_color', models.CharField(default='#1a1a2e', max_length=7)),
                ('wallpaper_color2', models.CharField(blank=True, default='', max_length=7)),
                ('pattern_type', models.CharField(blank=True, default='', max_length=20)),
                ('pattern_color', models.CharField(blank=True, default='', max_length=7)),
                ('pattern_opacity', models.IntegerField(default=20)),
                ('wallpaper_intensity', models.IntegerField(default=100)),
                ('wallpaper_blur', models.IntegerField(default=0)),
                ('wallpaper_motion', models.CharField(default='none', max_length=20)),
                ('gradient_angle', models.IntegerField(default=135)),
                ('wallpaper_image', models.ImageField(blank=True, null=True, upload_to='chat_wallpapers/')),
                ('is_preset', models.BooleanField(default=False)),
                ('preset_name', models.CharField(blank=True, max_length=100)),
                ('preset_category', models.CharField(blank=True, max_length=50)),
                ('dark_variant_color', models.CharField(blank=True, default='', max_length=7)),
                ('light_variant_color', models.CharField(blank=True, default='', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_wallpapers', to='users.user')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_wallpapers', to='social.groupchat')),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_wallpapers', to='social.privatechat')),
            ],
            options={'verbose_name': 'Обои чата'},
        ),
        migrations.AddIndex(model_name='chatwallpaper', index=models.Index(fields=['user','chat'], name='social_chatwallpaper_user_chat_idx')),
        migrations.AddIndex(model_name='chatwallpaper', index=models.Index(fields=['user','private_chat'], name='social_chatwallpaper_user_priv_idx')),
        migrations.AddIndex(model_name='chatwallpaper', index=models.Index(fields=['is_preset'], name='social_chatwallpaper_preset_idx')),

        # ── ChatTheme ──
        migrations.CreateModel(
            name='ChatTheme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(default='default', max_length=50)),
                ('message_color_mine', models.CharField(default='#3b82f6', max_length=7)),
                ('message_color_other', models.CharField(default='#2a2a3e', max_length=7)),
                ('message_text_color_mine', models.CharField(default='#ffffff', max_length=7)),
                ('message_text_color_other', models.CharField(default='#e2e8f0', max_length=7)),
                ('bubble_style', models.CharField(default='modern', max_length=20)),
                ('bubble_border_radius', models.IntegerField(default=18)),
                ('bubble_shadow', models.BooleanField(default=False)),
                ('font_family', models.CharField(default='system', max_length=30)),
                ('font_size', models.CharField(default='medium', max_length=10)),
                ('font_size_px', models.IntegerField(default=14)),
                ('font_weight', models.IntegerField(default=400)),
                ('line_height', models.FloatField(default=1.5)),
                ('time_format', models.CharField(default='24h', max_length=5)),
                ('time_color', models.CharField(default='rgba(255,255,255,0.5)', max_length=30)),
                ('background_color', models.CharField(default='#0f0f1a', max_length=7)),
                ('header_color', models.CharField(default='#1a1a2e', max_length=7)),
                ('input_color', models.CharField(default='#1e1e32', max_length=7)),
                ('input_text_color', models.CharField(default='#e2e8f0', max_length=7)),
                ('accent_color', models.CharField(default='#3b82f6', max_length=7)),
                ('link_color', models.CharField(default='#60a5fa', max_length=7)),
                ('message_animation', models.CharField(default='slide', max_length=20)),
                ('reaction_animation', models.CharField(default='bounce', max_length=20)),
                ('typing_animation', models.CharField(default='dots', max_length=20)),
                ('scroll_animation', models.CharField(default='smooth', max_length=20)),
                ('emoji_set', models.CharField(default='default', max_length=20)),
                ('emoji_size', models.CharField(default='medium', max_length=10)),
                ('show_avatars', models.BooleanField(default=True)),
                ('show_usernames', models.BooleanField(default=True)),
                ('compact_mode', models.BooleanField(default=False)),
                ('show_read_status', models.BooleanField(default=True)),
                ('show_typing_indicator', models.BooleanField(default=True)),
                ('message_grouping', models.BooleanField(default=True)),
                ('custom_css', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_themes', to='users.user')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_themes', to='social.groupchat')),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_themes', to='social.privatechat')),
            ],
            options={'verbose_name': 'Тема чата'},
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
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='social.privatechat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='private_chat_settings_v2', to='users.user')),
            ],
            options={'verbose_name': 'Настройки личного чата', 'unique_together': {('chat', 'user')}},
        ),
        migrations.AddIndex(model_name='privatechatsettings', index=models.Index(fields=['user','is_pinned'], name='social_pcs_user_pinned_idx')),
        migrations.AddIndex(model_name='privatechatsettings', index=models.Index(fields=['user','is_archived'], name='social_pcs_user_archived_idx')),

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
                ('membership', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='personal_settings', to='social.chatmember')),
            ],
            options={'verbose_name': 'Настройки участника группы'},
        ),

        # ── ChatBan ──
        migrations.CreateModel(
            name='ChatBan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('until_date', models.DateTimeField(blank=True, null=True)),
                ('delete_messages', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bans', to='social.groupchat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_bans', to='users.user')),
                ('banned_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issued_bans', to='users.user')),
            ],
            options={'verbose_name': 'Блокировка в чате', 'unique_together': {('chat', 'user')}},
        ),
        migrations.AddIndex(model_name='chatban', index=models.Index(fields=['chat','user'], name='social_chatban_chat_user_idx')),
        migrations.AddIndex(model_name='chatban', index=models.Index(fields=['until_date'], name='social_chatban_until_idx')),

        # ── ChatRestriction ──
        migrations.CreateModel(
            name='ChatRestriction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restriction_type', models.CharField(max_length=20)),
                ('reason', models.TextField(blank=True)),
                ('until_date', models.DateTimeField(blank=True, null=True)),
                ('slow_mode_delay', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='restrictions', to='social.groupchat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_restrictions', to='users.user')),
                ('restricted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issued_restrictions', to='users.user')),
            ],
            options={'verbose_name': 'Ограничение в чате'},
        ),

        # ── ChatSlowMode ──
        migrations.CreateModel(
            name='ChatSlowMode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False)),
                ('delay', models.IntegerField(default=30)),
                ('exempt_admins', models.BooleanField(default=True)),
                ('exempt_moderators', models.BooleanField(default=True)),
                ('custom_delays', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='slow_mode_settings', to='social.groupchat')),
            ],
            options={'verbose_name': 'Медленный режим'},
        ),

        # ── ChatJoinRequest ──
        migrations.CreateModel(
            name='ChatJoinRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True)),
                ('answers', models.JSONField(default=dict)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='join_requests', to='social.groupchat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_join_requests', to='users.user')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_join_requests', to='users.user')),
            ],
            options={'verbose_name': 'Запрос на вступление', 'unique_together': {('chat', 'user')}},
        ),

        # ── ChatTag ──
        migrations.CreateModel(
            name='ChatTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#3b82f6', max_length=7)),
                ('emoji', models.CharField(blank=True, max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_tags', to='users.user')),
            ],
            options={'verbose_name': 'Тег чата', 'unique_together': {('user', 'name')}},
        ),

        # ── ChatTagAssignment ──
        migrations.CreateModel(
            name='ChatTagAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='social.chattag')),
                ('group_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tag_assignments', to='social.groupchat')),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tag_assignments', to='social.privatechat')),
            ],
            options={'verbose_name': 'Привязка тега'},
        ),

        # ── AntiSpamRule ──
        migrations.CreateModel(
            name='AntiSpamRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_type', models.CharField(max_length=20)),
                ('threshold', models.IntegerField(default=5)),
                ('time_window', models.IntegerField(default=60)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('action', models.CharField(default='delete', max_length=20)),
                ('action_duration', models.IntegerField(blank=True, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='anti_spam_rules', to='social.groupchat')),
            ],
            options={'verbose_name': 'Правило анти-спама'},
        ),

        # ── MessageReaction ──
        migrations.CreateModel(
            name='MessageReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emoji', models.CharField(max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emoji_reactions', to='social.message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_emoji_reactions', to='users.user')),
            ],
            options={'verbose_name': 'Реакция', 'unique_together': {('message', 'user', 'emoji')}},
        ),
        migrations.AddIndex(model_name='messagereaction', index=models.Index(fields=['message','emoji'], name='social_msgreaction_msg_emoji_idx')),

        # ── MessagePin ──
        migrations.CreateModel(
            name='MessagePin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pinned_messages_v2', to='social.groupchat')),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pinned_messages_v2', to='social.privatechat')),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pin_info', to='social.message')),
                ('pinned_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pinned_messages_v2', to='users.user')),
            ],
            options={'verbose_name': 'Закреплённое сообщение'},
        ),

        # ── ChatBackup ──
        migrations.CreateModel(
            name='ChatBackup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backup_file', models.FileField(blank=True, null=True, upload_to='chat_backups/')),
                ('messages_count', models.IntegerField(default=0)),
                ('members_count', models.IntegerField(default=0)),
                ('file_size', models.BigIntegerField(default=0)),
                ('status', models.CharField(default='creating', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='backups', to='social.groupchat')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_backups', to='users.user')),
            ],
            options={'verbose_name': 'Резервная копия'},
        ),

        # ── ScheduledMessage ──
        migrations.CreateModel(
            name='ScheduledMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True)),
                ('media', models.FileField(blank=True, null=True, upload_to='scheduled_messages/')),
                ('media_type', models.CharField(blank=True, max_length=20)),
                ('scheduled_at', models.DateTimeField()),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurring_interval', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(default='scheduled', max_length=20)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_messages', to='users.user')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_messages', to='social.groupchat')),
                ('private_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_messages', to='social.privatechat')),
            ],
            options={'verbose_name': 'Запланированное сообщение'},
        ),
        migrations.AddIndex(model_name='scheduledmessage', index=models.Index(fields=['scheduled_at','status'], name='social_schedmsg_time_status_idx')),

        # ── SecurityLog ──
        migrations.CreateModel(
            name='SecurityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('device_info', models.JSONField(default=dict)),
                ('location', models.JSONField(default=dict)),
                ('details', models.JSONField(default=dict)),
                ('is_suspicious', models.BooleanField(default=False)),
                ('was_notified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_logs', to='users.user')),
            ],
            options={'verbose_name': 'Запись безопасности'},
        ),
        migrations.AddIndex(model_name='securitylog', index=models.Index(fields=['user','created_at'], name='social_seclog_user_time_idx')),

        # ── GroupChatSettings ──
        migrations.CreateModel(
            name='GroupChatSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('members_count', models.IntegerField(default=0)),
                ('online_count', models.IntegerField(default=0)),
                ('messages_count', models.IntegerField(default=0)),
                ('last_activity_at', models.DateTimeField(blank=True, null=True)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('permissions_cache', models.JSONField(default=dict)),
                ('daily_messages', models.IntegerField(default=0)),
                ('weekly_active', models.IntegerField(default=0)),
                ('cache_updated_at', models.DateTimeField(auto_now=True)),
                ('chat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cached_settings', to='social.groupchat')),
            ],
            options={'verbose_name': 'Настройки группы (кэш)'},
        ),
    ]
