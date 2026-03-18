#!/usr/bin/env python3
"""
repair_migration_0017.py
Запускать из корня проекта: /var/www/www-root/data/www/anisphere.ru/

Скрипт:
1. Находит файл 0017_*.py
2. Делает его резервную копию
3. Заменяет полным исправленным содержимым без проблемных операций
"""

import os
import glob
import shutil

migration_dir = 'social/migrations'
pattern = os.path.join(migration_dir, '0017_*.py')
files = glob.glob(pattern)

if not files:
    print("❌ Файл 0017_*.py не найден в", migration_dir)
    exit(1)

old_file = files[0]
backup_file = old_file + '.backup'
shutil.copy(old_file, backup_file)
print(f"✅ Резервная копия: {backup_file}")

# Полное правильное содержимое миграции
MIGRATION_CONTENT = '''# Generated and fixed migration for social chat settings
# Fix: removed rgba() defaults (MySQL incompatible), removed duplicate indexes

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("social", "0016_chatwallpaper_privatechatsettings_groupchatsettings_and_more"),
    ]

    operations = [
        # ── GroupMemberSettings ──
        migrations.CreateModel(
            name="GroupMemberSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notifications_enabled", models.BooleanField(default=True)),
                ("mentions_only", models.BooleanField(default=False)),
                ("sound_enabled", models.BooleanField(default=True)),
                ("show_preview", models.BooleanField(default=True)),
                ("muted_until", models.DateTimeField(blank=True, null=True)),
                ("is_pinned", models.BooleanField(default=False)),
                ("is_archived", models.BooleanField(default=False)),
                ("tags", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("membership", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="personal_settings",
                    to="social.chatmember",
                )),
            ],
            options={"verbose_name": "Настройки участника группы"},
        ),

        # ── Новые поля для ChatInviteLink ──
        migrations.AddField(
            model_name="chatinvitelink",
            name="link_type",
            field=models.CharField(
                choices=[("primary", "Основная"), ("temporary", "Временная"), ("personal", "Персональная")],
                default="temporary", max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="chatinvitelink",
            name="target_user",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="personal_invite_links",
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ── Новые поля ChatTheme (только HEX и безопасные значения) ──
        migrations.AddField(model_name="chattheme", name="accent_color",
            field=models.CharField(default="#3b82f6", max_length=7)),
        migrations.AddField(model_name="chattheme", name="background_color",
            field=models.CharField(default="#0f0f1a", max_length=7)),
        migrations.AddField(model_name="chattheme", name="bubble_border_radius",
            field=models.IntegerField(default=18)),
        migrations.AddField(model_name="chattheme", name="bubble_padding_x",
            field=models.IntegerField(default=12)),
        migrations.AddField(model_name="chattheme", name="bubble_padding_y",
            field=models.IntegerField(default=8)),
        migrations.AddField(model_name="chattheme", name="bubble_shadow",
            field=models.BooleanField(default=False)),

        # bubble_shadow_color: rgba — null=True, без DEFAULT в БД
        migrations.AddField(model_name="chattheme", name="bubble_shadow_color",
            field=models.CharField(max_length=30, null=True, blank=True)),

        migrations.AddField(model_name="chattheme", name="compact_mode",
            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="chattheme", name="custom_css",
            field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="chattheme", name="font_family",
            field=models.CharField(default="system", max_length=30)),
        migrations.AddField(model_name="chattheme", name="font_size_px",
            field=models.IntegerField(default=14)),
        migrations.AddField(model_name="chattheme", name="font_weight",
            field=models.IntegerField(default=400)),
        migrations.AddField(model_name="chattheme", name="header_color",
            field=models.CharField(default="#1a1a2e", max_length=7)),
        migrations.AddField(model_name="chattheme", name="input_color",
            field=models.CharField(default="#1e1e32", max_length=7)),
        migrations.AddField(model_name="chattheme", name="input_text_color",
            field=models.CharField(default="#e2e8f0", max_length=7)),
        migrations.AddField(model_name="chattheme", name="line_height",
            field=models.FloatField(default=1.5)),
        migrations.AddField(model_name="chattheme", name="link_color",
            field=models.CharField(default="#60a5fa", max_length=7)),
        migrations.AddField(model_name="chattheme", name="message_grouping",
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name="chattheme", name="message_text_color_mine",
            field=models.CharField(default="#ffffff", max_length=7)),
        migrations.AddField(model_name="chattheme", name="message_text_color_other",
            field=models.CharField(default="#e2e8f0", max_length=7)),
        migrations.AddField(model_name="chattheme", name="scroll_animation",
            field=models.CharField(default="smooth", max_length=20)),
        migrations.AddField(model_name="chattheme", name="show_avatars",
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name="chattheme", name="show_read_status",
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name="chattheme", name="show_seconds",
            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="chattheme", name="show_typing_indicator",
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name="chattheme", name="show_usernames",
            field=models.BooleanField(default=True)),

        # time_color: rgba — null=True, без DEFAULT в БД
        migrations.AddField(model_name="chattheme", name="time_color",
            field=models.CharField(max_length=30, null=True, blank=True)),

        # ── Новые поля ChatWallpaper ──
        migrations.AddField(model_name="chatwallpaper", name="dark_variant_color",
            field=models.CharField(blank=True, default="", max_length=7)),
        migrations.AddField(model_name="chatwallpaper", name="gradient_angle",
            field=models.IntegerField(default=135)),
        migrations.AddField(model_name="chatwallpaper", name="light_variant_color",
            field=models.CharField(blank=True, default="", max_length=7)),
        migrations.AddField(model_name="chatwallpaper", name="pattern_color",
            field=models.CharField(blank=True, default="", max_length=7)),
        migrations.AddField(model_name="chatwallpaper", name="pattern_opacity",
            field=models.IntegerField(default=20)),
        migrations.AddField(model_name="chatwallpaper", name="pattern_type",
            field=models.CharField(blank=True, default="", max_length=20)),
        migrations.AddField(model_name="chatwallpaper", name="preset_category",
            field=models.CharField(blank=True, max_length=50)),

        # ── Новые поля PrivateChatSettings ──
        migrations.AddField(model_name="privatechatsettings", name="auto_delete_enabled",
            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="privatechatsettings", name="blocked_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="privatechatsettings", name="notification_sound",
            field=models.CharField(default="default", max_length=50)),
        migrations.AddField(model_name="privatechatsettings", name="tags",
            field=models.JSONField(default=list)),
        migrations.AddField(model_name="privatechatsettings", name="vibration_type",
            field=models.CharField(default="default", max_length=20)),

        # ── Alter fields ──
        migrations.AlterField(model_name="chattheme", name="message_color_mine",
            field=models.CharField(default="#3b82f6", max_length=7, verbose_name="Цвет своих сообщений")),

        # ── unique_together ──
        migrations.AlterUniqueTogether(name="chatban",
            unique_together={("chat", "user")}),

        # ── Индекс для chatwallpaper.is_preset ──
        migrations.AddIndex(model_name="chatwallpaper",
            index=models.Index(fields=["is_preset"], name="social_chat_is_pres_5b84e0_idx")),

        # ── Индекс для privatechatsettings.user + is_hidden ──
        migrations.AddIndex(model_name="privatechatsettings",
            index=models.Index(fields=["user", "is_hidden"], name="social_priv_user_id_c9e0f1_idx")),
    ]
'''

with open(old_file, 'w', encoding='utf-8') as f:
    f.write(MIGRATION_CONTENT)

print(f"✅ Файл перезаписан: {old_file}")
print("\nТеперь нужно проверить зависимость (dependencies) — убедитесь что 0016 существует.")
print("Запустите: python manage.py showmigrations social")
print("Если 0016 нет — измените dependencies на правильную предыдущую миграцию.")
