#!/bin/bash
# =============================================================
# ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ МИГРАЦИИ 0017 НА СЕРВЕРЕ
# Запускать из: /var/www/www-root/data/www/anisphere.ru/
#   bash fix_all_migrations.sh
# =============================================================

set -e
cd /var/www/www-root/data/www/anisphere.ru

echo "======================================"
echo "  ИСПРАВЛЕНИЕ МИГРАЦИЙ ЧАТОВ"
echo "======================================"

# ── Шаг 1: Показать текущее состояние ──
echo ""
echo "📋 Текущие миграции social:"
python manage.py showmigrations social 2>/dev/null | tail -20

# ── Шаг 2: Найти файл 0017 ──
MIG_FILE=$(ls social/migrations/0017_*.py 2>/dev/null | head -1)
if [ -z "$MIG_FILE" ]; then
    echo "❌ Файл 0017_*.py не найден"
    exit 1
fi
echo ""
echo "📄 Файл миграции: $MIG_FILE"

# ── Шаг 3: Резервная копия ──
cp "$MIG_FILE" "${MIG_FILE}.bak_$(date +%s)"
echo "✅ Резервная копия создана"

# ── Шаг 4: Применяем Python-скрипт исправления ──
echo ""
echo "🔧 Применяю исправления..."
python3 - <<'PYEOF'
import re, glob, sys

fname = glob.glob('social/migrations/0017_*.py')[0]
with open(fname) as f:
    content = f.read()

original = content
changes = []

# Фикс 1: rgba() defaults -> null=True, blank=True
count = len(re.findall(r"default='rgba", content))
if count:
    content = re.sub(r"default='rgba\([^']+\)'", "null=True, blank=True", content)
    changes.append(f"  ✅ Исправлено {count} rgba() default значений")

# Фикс 2: убираем RemoveIndex операции (вызывают Duplicate key)
remove_index_count = len(re.findall(r'migrations\.RemoveIndex\(', content))
if remove_index_count:
    # Многострочный RemoveIndex
    content = re.sub(
        r'\s*migrations\.RemoveIndex\([^)]+\),',
        '',
        content
    )
    changes.append(f"  ✅ Удалено {remove_index_count} RemoveIndex операций")

# Фикс 3: убираем дублирующийся AddIndex для messagepin.chat_id
dup_count = len(re.findall(r"AddIndex.*messagepin.*chat_id", content, re.DOTALL))
if dup_count:
    content = re.sub(
        r'\s*migrations\.AddIndex\(\s*\n\s*model_name=["\']messagepin["\'],\s*\n\s*index=models\.Index\(fields=\["chat"\][^)]+\)[^)]*\),',
        '',
        content
    )
    changes.append(f"  ✅ Удалено {dup_count} дублирующихся AddIndex")

if content != original:
    with open(fname, 'w') as f:
        f.write(content)
    print('\n'.join(changes))
    print(f"\n✅ Файл исправлен: {fname}")
else:
    print("⚠️  Изменений не внесено — возможно паттерны уже исправлены")
    # Показываем строки с rgba
    for i, line in enumerate(original.splitlines(), 1):
        if 'rgba' in line.lower() or 'RemoveIndex' in line:
            print(f"  Строка {i}: {line.strip()[:100]}")
PYEOF

# ── Шаг 5: Запуск migrate ──
echo ""
echo "======================================"
echo "🚀 python manage.py migrate social"
echo "======================================"
python manage.py migrate social

echo ""
echo "======================================"
echo "✅ ГОТОВО"
echo "======================================"
