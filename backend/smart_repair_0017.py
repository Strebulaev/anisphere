#!/usr/bin/env python3
"""
smart_repair_0017.py — умный ремонт миграции 0017.

Запускать из: /var/www/www-root/data/www/anisphere.ru/
    python smart_repair_0017.py

Что делает:
1. Находит предыдущую миграцию (0016 или другую)
2. Читает текущий 0017, исправляет только проблемные строки
3. Применяет migrate
"""

import os
import re
import glob
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATION_DIR = os.path.join(BASE_DIR, 'social', 'migrations')


def get_previous_migration():
    """Найти предыдущую миграцию перед 0017"""
    files = sorted(glob.glob(os.path.join(MIGRATION_DIR, '0[0-9][0-9][0-9]_*.py')))
    for i, f in enumerate(files):
        name = os.path.basename(f)
        if name.startswith('0017_'):
            if i > 0:
                prev = os.path.basename(files[i-1])
                return prev.replace('.py', '')
    # Если не нашли — берём максимальный до 0017
    for f in reversed(sorted(glob.glob(os.path.join(MIGRATION_DIR, '0[0-9][0-9][0-9]_*.py')))):
        name = os.path.basename(f)
        num = int(name[:4])
        if num < 17:
            return name.replace('.py', '')
    return None


def get_0017_file():
    files = glob.glob(os.path.join(MIGRATION_DIR, '0017_*.py'))
    return files[0] if files else None


def fix_migration_content(content: str, prev_migration: str) -> str:
    """
    Исправляет содержимое миграции:
    1. rgba() default -> null=True, blank=True
    2. Дублирующиеся индексы -> убираем RemoveIndex для уже удалённых
    """

    # ── Фикс 1: rgba дефолты ──
    # default='rgba(255,255,255,0.5)' -> null=True, blank=True
    content = re.sub(
        r",\s*default='rgba\([^']*\)'",
        ', null=True, blank=True',
        content
    )
    content = re.sub(
        r"default='rgba\([^']*\)',?\s*",
        'null=True, blank=True, ',
        content
    )
    # Убираем двойные null=True
    content = re.sub(r'null=True,\s*blank=True,\s*null=True,\s*blank=True', 'null=True, blank=True', content)

    # ── Фикс 2: исправить зависимость если надо ──
    if prev_migration and prev_migration not in content:
        content = re.sub(
            r'("social",\s*")[^"]*(")',
            f'\\g<1>{prev_migration}\\g<2>',
            content,
            count=1
        )

    # ── Фикс 3: убрать RemoveIndex операции для индексов MessagePin
    # Они уже были удалены в предыдущей миграции или не существуют
    # Ищем RemoveIndex для messagepin и убираем их
    problematic_remove_patterns = [
        r'migrations\.RemoveIndex\(\s*model_name=["\']messagepin["\'],\s*name=["\'][^"\']*["\'],?\s*\),?\s*',
        r'migrations\.RemoveIndex\(\s*model_name=["\']scheduledmessage["\'],\s*name=["\'][^"\']*["\'],?\s*\),?\s*',
        r'migrations\.RemoveIndex\(\s*model_name=["\']securitylog["\'],\s*name=["\'][^"\']*["\'],?\s*\),?\s*',
    ]
    for pattern in problematic_remove_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # ── Фикс 4: убрать дублирующиеся AddIndex для уже существующих индексов ──
    # social_messagepin_chat_id_3257e9d9 — уже существует, убираем попытку создать
    dup_index_patterns = [
        r'migrations\.AddIndex\(\s*model_name=["\']messagepin["\'],\s*index=models\.Index\([^)]*chat_id[^)]*\)[^)]*\),?\s*',
        r'migrations\.AddIndex\(\s*model_name=["\']messagepin["\'],\s*index=models\.Index\([^)]*private_chat[^)]*\)[^)]*\),?\s*',
    ]
    for pattern in dup_index_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    return content


def main():
    mig_file = get_0017_file()
    if not mig_file:
        print("❌ Файл 0017_*.py не найден")
        return False

    prev = get_previous_migration()
    print(f"📄 Исправляю: {os.path.basename(mig_file)}")
    print(f"📌 Предыдущая миграция: {prev}")

    # Резервная копия
    backup = mig_file + '.bak2'
    import shutil
    shutil.copy(mig_file, backup)
    print(f"💾 Резервная копия: {os.path.basename(backup)}")

    with open(mig_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Показываем проблемные строки
    print("\n🔍 Найдены проблемные строки:")
    for i, line in enumerate(content.splitlines(), 1):
        if 'rgba' in line.lower():
            print(f"  rgba на строке {i}: {line.strip()[:80]}")
        if 'RemoveIndex' in line and ('messagepin' in line.lower() or 'scheduledmessage' in line.lower()):
            print(f"  RemoveIndex на строке {i}: {line.strip()[:80]}")

    fixed = fix_migration_content(content, prev)

    with open(mig_file, 'w', encoding='utf-8') as f:
        f.write(fixed)

    print(f"\n✅ Файл исправлен!")

    # Проверка синтаксиса
    result = subprocess.run([sys.executable, '-m', 'py_compile', mig_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  Синтаксическая ошибка: {result.stderr}")
        shutil.copy(backup, mig_file)
        print("↩️  Восстановлена резервная копия")
        return False

    print("✅ Синтаксис OK")
    return True


if __name__ == '__main__':
    success = main()
    if success:
        print("\n🚀 Запускаю migrate...")
        os.system(f"{sys.executable} manage.py migrate social")
    else:
        print("\n❌ Исправление не удалось. Попробуйте ручное редактирование.")
