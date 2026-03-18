#!/bin/bash
# fix_migration_mysql.sh
# Исправляет ошибку "Invalid default value for time_color" в MySQL
# Запускать из /var/www/www-root/data/www/anisphere.ru/

set -e

MIGRATION_FILE=$(ls social/migrations/0017_*.py 2>/dev/null | head -1)

if [ -z "$MIGRATION_FILE" ]; then
    echo "❌ Файл миграции 0017_*.py не найден"
    exit 1
fi

echo "📄 Файл: $MIGRATION_FILE"

# Резервная копия
cp "$MIGRATION_FILE" "${MIGRATION_FILE}.bak"
echo "✅ Резервная копия: ${MIGRATION_FILE}.bak"

# Исправление: заменяем все вхождения rgba в default на null=True, blank=True
# Паттерн 1: default='rgba(...)'  -->  null=True, blank=True
python3 - <<'EOF'
import re
import sys

fname = sys.argv[1] if len(sys.argv) > 1 else None

import glob
files = glob.glob('social/migrations/0017_*.py')
if not files:
    print("File not found")
    sys.exit(1)

fname = files[0]

with open(fname, 'r') as f:
    content = f.read()

original = content

# Находим все AddField/AlterField для time_color и bubble_shadow_color
# и убираем default с rgba значениями

# Паттерн: убираем default='rgba(...)' из CharField определений
# Заменяем на null=True, blank=True
content = re.sub(
    r"(field=models\.CharField\([^)]*?)default='rgba\([^']+\)'([^)]*?\))",
    lambda m: m.group(1).rstrip(', ') + ', null=True, blank=True' + m.group(2),
    content
)

# Паттерн 2 — другой порядок аргументов
content = re.sub(
    r"default='rgba\([^']+\)'",
    "null=True, blank=True",
    content
)

if content == original:
    print("⚠️  Паттерн rgba не найден — проверьте файл вручную")
    # Показываем строки с rgba
    for i, line in enumerate(original.splitlines(), 1):
        if 'rgba' in line:
            print(f"  Строка {i}: {line.strip()}")
else:
    with open(fname, 'w') as f:
        f.write(content)
    print(f"✅ Исправлено в файле: {fname}")
EOF

echo ""
echo "🚀 Запускаем migrate..."
python manage.py migrate social

echo "✅ Готово!"
