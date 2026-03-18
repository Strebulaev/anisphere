#!/usr/bin/env python3
"""
fix_0017_final.py — финальное исправление миграции 0017
Запускать из: /var/www/www-root/data/www/anisphere.ru/
    python fix_0017_final.py

Исправляет ВСЕ известные проблемы:
1. rgba() defaults → null=True, blank=True
2. Дублирующийся индекс social_messagepin_chat_id_3257e9d9
3. Другие RemoveIndex/AddIndex конфликты
"""

import os, re, glob, shutil, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
MIG_DIR = os.path.join(BASE, 'social', 'migrations')

# ── Найти файл 0017 ──
files_0017 = glob.glob(os.path.join(MIG_DIR, '0017_*.py'))
if not files_0017:
    sys.exit("❌ Файл 0017_*.py не найден")

mig_file = files_0017[0]
print(f"Файл: {mig_file}")

# ── Резервная копия ──
bak = mig_file + '.bak_final'
shutil.copy(mig_file, bak)
print(f"Резервная копия: {bak}")

# ── Читаем файл ──
with open(mig_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Строк в файле: {len(lines)}")

# ── Показываем все проблемные строки ──
print("\nПроблемные строки:")
for i, line in enumerate(lines, 1):
    if 'rgba' in line:
        print(f"  [rgba]  #{i}: {line.rstrip()[:100]}")
    if 'RemoveIndex' in line:
        print(f"  [RemoveIndex] #{i}: {line.rstrip()[:100]}")

# ── Стратегия исправления ──
# Вместо тонких regex — обрабатываем блоки

content = ''.join(lines)

# ── Фикс 1: убираем ВСЕ RemoveIndex операции (они падают на дубликатах) ──
# Паттерн: migrations.RemoveIndex( ... ),
content = re.sub(
    r'migrations\.RemoveIndex\([^)]+\),?\s*\n',
    '',
    content
)
# Многострочный вариант
content = re.sub(
    r'migrations\.RemoveIndex\(.*?\),\s*\n',
    '',
    content,
    flags=re.DOTALL
)

# ── Фикс 2: rgba() → null=True, blank=True ──
# Паттерн 1: default='rgba(...)'
content = re.sub(r"default='rgba\([^']+\)'", "null=True, blank=True", content)
# Паттерн 2: default="rgba(...)"
content = re.sub(r'default="rgba\([^"]+\)"', "null=True, blank=True", content)

# ── Фикс 3: AddIndex для messagepin chat_id — уже существует, убираем ──
# Находим блоки AddIndex для messagepin с chat_id и private_chat_id
def remove_add_index_block(text, model, field_hint):
    """Убирает migrations.AddIndex для конкретной модели и поля"""
    # Паттерн: migrations.AddIndex(\n    model_name="messagepin",\n    index=models.Index(fields=["chat"...
    pattern = (
        r'migrations\.AddIndex\(\s*\n'
        r'\s*model_name=["\']' + re.escape(model) + r'["\'],\s*\n'
        r'\s*index=models\.Index\([^)]*' + re.escape(field_hint) + r'[^)]*\)[^)]*\),\s*\n'
    )
    return re.sub(pattern, '', text, flags=re.DOTALL)

# Убираем AddIndex для messagepin.chat (уже существует из предыдущей миграции)
content = remove_add_index_block(content, 'messagepin', 'chat')

# ── Фикс 4: убираем двойные запятые и пустые строки внутри operations ──
# Множественные запятые: ,, → ,
content = re.sub(r',\s*,', ',', content)
# Двойные пустые строки внутри operations
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

# ── Записываем ──
with open(mig_file, 'w', encoding='utf-8') as f:
    f.write(content)
print("\n✅ Файл записан")

# ── Проверка синтаксиса Python ──
r = subprocess.run([sys.executable, '-m', 'py_compile', mig_file], capture_output=True, text=True)
if r.returncode != 0:
    print(f"⚠️  Синтаксическая ошибка:\n{r.stderr}")
    shutil.copy(bak, mig_file)
    print("↩️  Восстановлена резервная копия")
    print("\nПопробуйте ручное редактирование файла:")
    print(f"  nano {mig_file}")
    sys.exit(1)

print("✅ Синтаксис Python OK")

# ── Запускаем migrate ──
print("\n" + "="*50)
print("Запуск: python manage.py migrate social")
print("="*50)
ret = os.system(f"{sys.executable} manage.py migrate social")
if ret == 0:
    print("\n✅ Миграция применена успешно!")
else:
    print(f"\n❌ migrate завершился с кодом {ret}")
    print("Просмотрите ошибку выше и при необходимости восстановите резервную копию:")
    print(f"  cp {bak} {mig_file}")
