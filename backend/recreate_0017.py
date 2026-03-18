#!/usr/bin/env python3
"""
recreate_0017.py — полностью пересоздаёт миграцию 0017.

Запускать из: /var/www/www-root/data/www/anisphere.ru/
    python recreate_0017.py

1. Определяет предыдущую миграцию
2. Удаляет проблемный файл 0017
3. Помечает фейковую точку (fake migration)
4. Пересоздаёт правильный файл
"""

import os, glob, re, sys, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
MIG_DIR = os.path.join(BASE, 'social', 'migrations')

# ── 1. Найти предыдущую миграцию ──
all_migs = sorted(
    [os.path.basename(f) for f in glob.glob(os.path.join(MIG_DIR, '0[0-9][0-9][0-9]_*.py'))]
)
print("Все миграции:", all_migs)

prev_mig = None
for m in all_migs:
    num = int(m[:4])
    if num < 17:
        prev_mig = m.replace('.py', '')

print(f"Предыдущая миграция: {prev_mig}")

# ── 2. Найти и удалить файл 0017 ──
files_0017 = glob.glob(os.path.join(MIG_DIR, '0017_*.py'))
for f in files_0017:
    bak = f + '.deleted'
    shutil.copy(f, bak)
    os.remove(f)
    print(f"Удалён (с резервной копией): {f}")
    print(f"Резервная копия: {bak}")

# ── 3. Генерируем правильный файл 0017 ──
new_content = f'''# Fixed migration 0017 - MySQL compatible, no duplicate indexes
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("social", "{prev_mig}"),
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
                (
                    "membership",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_settings",
                        to="social.chatmember",
                    ),
                ),
            ],
            options={{"verbose_name": "\\u041d\\u0430\\u0441\\u0442\\u0440\\u043e\\u0439\\u043a\\u0438 \\u0443\\u0447\\u0430\\u0441\\u0442\\u043d\\u0438\\u043a\\u0430 \\u0433\\u0440\\u0443\\u043f\\u043f\\u044b"}},
        ),

        # ── ChatInviteLink: новые поля ──
        migrations.AddField(
            model_name="chatinvitelink",
            name="link_type",
            field=models.CharField(
                choices=[("primary", "\\u041e\\u0441\\u043d\\u043e\\u0432\\u043d\\u0430\\u044f"),
                         ("temporary", "\\u0412\\u0440\\u0435\\u043c\\u0435\\u043d\\u043d\\u0430\\u044f"),
                         ("personal", "\\u041f\\u0435\\u0440\\u0441\\u043e\\u043d\\u0430\\u043b\\u044c\\u043d\\u0430\\u044f")],
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

        # ── ChatTheme: новые поля (только MySQL-безопасные defaults) ──
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

        # bubble_shadow_color содержит rgba() — null=True без DEFAULT в БД
        migrations.AddField(model_name="chattheme", name="bubble_shadow_color",
            field=models.CharField(blank=True, max_length=30, null=True)),

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

        # time_color содержит rgba() — null=True без DEFAULT в БД
        migrations.AddField(model_name="chattheme", name="time_color",
            field=models.CharField(blank=True, max_length=30, null=True)),

        # ── ChatWallpaper: новые поля ──
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

        # ── PrivateChatSettings: новые поля ──
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

        # ── AlterField: message_color_mine (переименован) ──
        migrations.AlterField(
            model_name="chattheme",
            name="message_color_mine",
            field=models.CharField(default="#3b82f6", max_length=7),
        ),

        # ── unique_together для chatban ──
        migrations.AlterUniqueTogether(
            name="chatban",
            unique_together={{("chat", "user")}},
        ),

        # ── Индексы (только новые, не дублирующие существующие) ──
        migrations.AddIndex(
            model_name="chatwallpaper",
            index=models.Index(fields=["is_preset"], name="social_chat_is_pres_5b84e0_idx"),
        ),
        migrations.AddIndex(
            model_name="privatechatsettings",
            index=models.Index(fields=["user", "is_hidden"], name="social_priv_user_id_c9e0f1_idx"),
        ),
    ]
'''

new_file = os.path.join(MIG_DIR, '0017_chat_settings_mysql_fixed.py')
with open(new_file, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f"\n✅ Создан новый файл: {new_file}")

# ── 4. Проверка синтаксиса ──
r = subprocess.run([sys.executable, '-m', 'py_compile', new_file], capture_output=True, text=True)
if r.returncode != 0:
    print(f"⚠️  Синтаксическая ошибка:\n{r.stderr}")
    sys.exit(1)
print("✅ Синтаксис OK")

# ── 5. Запускаем migrate ──
print("\n" + "="*60)
print("Запуск: python manage.py migrate social")
print("="*60 + "\n")
ret = os.system(f'"{sys.executable}" manage.py migrate social')
sys.exit(0 if ret == 0 else 1)
