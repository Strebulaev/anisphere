#!/bin/bash
# Скрипт диагностики миграций на сервере
# Запустить: bash /tmp/check_migrations.sh

cd /var/www/www-root/data/www/anisphere.ru
source venv/bin/activate

echo "=== Применённые миграции anime ==="
python manage.py showmigrations anime 2>/dev/null | grep '\[X\]'

echo ""
echo "=== Все файлы миграций ==="
ls -la anime/migrations/*.py | grep -v __pycache__

echo ""
echo "=== Таблицы в БД (anime_*) ==="
python manage.py dbshell <<'EOF'
SELECT tablename FROM pg_tables WHERE tablename LIKE 'anime_%' ORDER BY tablename;
EOF
