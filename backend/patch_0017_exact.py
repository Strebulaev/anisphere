#!/usr/bin/env python3
"""
patch_0017_exact.py — точечное исправление файла 0017.

Проблема 1: default='rgba(255,255,255,0.5)' для time_color
Проблема 2: Duplicate key 'social_messagepin_chat_id_3257e9d9'
            (RemoveIndex пытается удалить несуществующий индекс,
             потом MySQL при удалении ищет FK индекс и не может создать — дубликат)

Решение: убрать все RemoveIndex и проблемные AddIndex
"""

import glob, re, sys, subprocess, shutil, os

BASE = os.getcwd()
MIG_DIR = os.path.join(BASE, 'social', 'migrations')

files = glob.glob(os.path.join(MIG_DIR, '0017_*.py'))
if not files:
    sys.exit("Файл 0017 не найден")

fname = files[0]
print(f"Файл: {fname}")

with open(fname) as f:
    text = f.read()

# Бэкап
shutil.copy(fname, fname + '.exact_bak')

orig = text

# ═══════════════════════════════════════════════════
# ПАТЧ 1: убираем ВСЕ RemoveIndex (они все проблемные)
# ═══════════════════════════════════════════════════
# Шаблон: однострочные и многострочные

# Сначала попробуем найти их
remove_idx = re.findall(r'migrations\.RemoveIndex\(.*?\),', text, re.DOTALL)
print(f"\nНайдено RemoveIndex: {len(remove_idx)}")
for ri in remove_idx:
    print(f"  - {ri[:80].strip()}")

# Убираем все RemoveIndex блоки
text = re.sub(r'\s*migrations\.RemoveIndex\(.*?\),', '', text, flags=re.DOTALL)

# ═══════════════════════════════════════════════════
# ПАТЧ 2: убираем rgba() дефолты
# ═══════════════════════════════════════════════════
rgba_fields = re.findall(r"default='rgba[^']*'", text)
print(f"\nНайдено rgba defaults: {len(rgba_fields)}")
for rf in rgba_fields:
    print(f"  - {rf}")

text = re.sub(r"default='rgba\([^']+\)'", "null=True, blank=True", text)
text = re.sub(r'default="rgba\([^"]+\)"', "null=True, blank=True", text)

# ═══════════════════════════════════════════════════
# ПАТЧ 3: убираем AddIndex для messagepin которые дублируются
# ═══════════════════════════════════════════════════
# Ищем AddIndex для messagepin
mp_indexes = re.findall(
    r'migrations\.AddIndex\(\s*\n?\s*model_name=["\']messagepin["\'][^\)]*\)',
    text, re.DOTALL
)
print(f"\nНайдено AddIndex для messagepin: {len(mp_indexes)}")

# Убираем AddIndex для messagepin если такие индексы уже существуют
# (chat_id и private_chat_id — они были добавлены в предыдущей миграции)
text = re.sub(
    r'\s*migrations\.AddIndex\(\s*\n\s*model_name=["\']messagepin["\'],\s*\n\s*index=models\.Index\(fields=\["chat"\].*?\),',
    '',
    text,
    flags=re.DOTALL
)
text = re.sub(
    r'\s*migrations\.AddIndex\(\s*\n\s*model_name=["\']messagepin["\'],\s*\n\s*index=models\.Index\(fields=\["private_chat"\].*?\),',
    '',
    text,
    flags=re.DOTALL
)

# ═══════════════════════════════════════════════════
# Проверяем и сохраняем
# ═══════════════════════════════════════════════════
if text != orig:
    with open(fname, 'w') as f:
        f.write(text)
    print(f"\n✅ Файл обновлён")
else:
    print("\n⚠️  Изменений не внесено — файл уже исправлен или паттерны не найдены")
    print("Содержимое файла (первые 100 строк):")
    for i, line in enumerate(orig.splitlines()[:100], 1):
        print(f"{i:4}: {line}")
    sys.exit(0)

# Проверка синтаксиса
r = subprocess.run([sys.executable, '-m', 'py_compile', fname], capture_output=True, text=True)
if r.returncode != 0:
    print(f"\n❌ Синтаксическая ошибка: {r.stderr}")
    shutil.copy(fname + '.exact_bak', fname)
    sys.exit(1)

print("✅ Синтаксис OK")
print("\nЗапускаю migrate...")
ret = os.system(f"{sys.executable} manage.py migrate social")
if ret != 0:
    print(f"\n❌ migrate завершился с кодом {ret}")
    # Показать оставшиеся проблемные строки
    with open(fname) as f:
        for i, line in enumerate(f, 1):
            if 'rgba' in line.lower() or 'RemoveIndex' in line:
                print(f"  Строка {i}: {line.rstrip()}")
