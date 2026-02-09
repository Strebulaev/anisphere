#!/bin/bash

# Скрипт для запуска аниме-платформы с anime-parsers-ru

echo "🎬 Запуск аниме-платформы с anime-parsers-ru..."
echo "============================================="

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

echo "✅ Docker найден"

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down

# Строим и запускаем контейнеры
echo "🏗️ Строим и запускаем контейнеры..."
docker-compose up --build -d

# Ждем, пока база данных будет готова
echo "⏳ Ожидаем готовности базы данных..."
sleep 10

# Применяем миграции
echo "📋 Применяем миграции..."
docker-compose exec -T backend python manage.py migrate

# Создаем тестовые данные (опционально)
echo "📊 Создаем тестовые данные..."
docker-compose exec -T backend python manage.py loaddata test_data.json 2>/dev/null || echo "⚠️ Тестовые данные не найдены, пропускаем"

echo ""
echo "🎉 Аниме-платформа успешно запущена!"
echo "============================================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Документация: http://localhost:8000/api/docs/"
echo "⚙️ Админ-панель: http://localhost:8000/admin/"
echo ""
echo "🔍 Поиск аниме: http://localhost:3000/search"
echo "📺 Список аниме: http://localhost:3000/anime"
echo ""
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "🔍 Для просмотра логов: docker-compose logs -f"
echo "🛑 Для остановки: docker-compose down"
echo "🔄 Для перезапуска: docker-compose restart"
echo ""
echo "✨ Готово к использованию!"