#!/bin/bash
# Полное исправление миграций на сервере
# ЗАПУСТИТЬ: bash /tmp/fix_migrations.sh

set -e
cd /var/www/www-root/data/www/anisphere.ru
source venv/bin/activate

echo "=== ШАГ 1: Смотрим что применено ==="
python manage.py showmigrations anime 2>/dev/null

echo ""
echo "=== ШАГ 2: Удаляем проблемные merge-миграцию если она есть ==="
rm -f anime/migrations/0015_merge_*.py
echo "Удалено (если было)"

echo ""
echo "=== ШАГ 3: Проверяем есть ли таблица UserEpisodeProgress ==="
python manage.py dbshell << 'DBEOF'
SELECT EXISTS (
  SELECT FROM information_schema.tables 
  WHERE table_name = 'anime_userepisodeprogress'
);
DBEOF
