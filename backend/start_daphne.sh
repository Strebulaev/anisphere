#!/bin/bash
# Запуск Daphne ASGI сервера для WebSocket
# Должен работать на порту 8002

cd /var/www/www-root/data/www/anisphere.ru/backend

# Активируем виртуальное окружение если есть
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Устанавливаем переменные окружения
export DJANGO_SETTINGS_MODULE=config.settings

# Запускаем Daphne на порту 8002
exec daphne -b 127.0.0.1 -p 8002 config.asgi:application
