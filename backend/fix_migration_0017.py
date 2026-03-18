#!/usr/bin/env python3
"""
Скрипт для исправления ошибки MySQL в миграции 0017.
Запускать из директории /var/www/www-root/data/www/anisphere.ru/

Использование:
    python fix_migration_0017.py
"""

import os
import re
import glob

# Ищем файл миграции 0017
migration_dir = os.path.join(os.path.dirname(__file__), 'social', 'migrations')
pattern = os.path.join(migration_dir, '0017_*.py')
files = glob.glob(pattern)

if not files:
    print("❌ Файл миграции 0017 не найден")
    exit(1)

migration_file = files[0]
print(f"✅ Найден файл: {migration_file}")

with open(migration_file, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Исправление 1: time_color с rgba default
# Меняем: default='rgba(255,255,255,0.5)'
# На: null=True, blank=True (без default в БД)
content = re.sub(
    r"(models\.CharField\([^)]*)'rgba\(255,255,255,0\.5\)'([^)]*)\)",
    lambda m: m.group(0).replace("default='rgba(255,255,255,0.5)'", "null=True, blank=True"),
    content
)

# Исправление 2: bubble_shadow_color с rgba default
content = re.sub(
    r"(models\.CharField\([^)]*)'rgba\(0,0,0,0\.2\)'([^)]*)\)",
    lambda m: m.group(0).replace("default='rgba(0,0,0,0.2)'", "null=True, blank=True"),
    content
)

# Более общий паттерн — убрать любой default с rgba(...)
# Находим AddField операции с time_color и bubble_shadow_color
def fix_rgba_default(match):
    field_def = match.group(0)
    # Убираем default='rgba(...)' и заменяем на null=True, blank=True
    field_def = re.sub(r",\s*default='rgba\([^']+\)'", ', null=True, blank=True', field_def)
    field_def = re.sub(r"default='rgba\([^']+\)',\s*", 'null=True, blank=True, ', field_def)
    return field_def

content = re.sub(
    r"models\.CharField\([^)]*rgba[^)]*\)",
    fix_rgba_default,
    content
)

if content == original:
    print("⚠️  Никаких изменений не внесено. Проверьте содержимое файла вручную.")
    print("\nПоиск rgba в файле:")
    for i, line in enumerate(original.split('\n'), 1):
        if 'rgba' in line.lower():
            print(f"  Строка {i}: {line.strip()}")
else:
    backup = migration_file + '.bak'
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"✅ Резервная копия сохранена: {backup}")

    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Файл исправлен: {migration_file}")

print("\nТеперь запустите: python manage.py migrate social")
