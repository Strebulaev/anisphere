# Скрипт для запуска аниме-платформы с anime-parsers-ru (Windows PowerShell)

Write-Host "🎬 Запуск аниме-платформы с anime-parsers-ru..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Yellow

# Проверяем Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен. Пожалуйста, установите Docker." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose." -ForegroundColor Red
    exit 1
}

# Останавливаем существующие контейнеры
Write-Host "🛑 Останавливаем существующие контейнеры..." -ForegroundColor Yellow
docker-compose down

# Строим и запускаем контейнеры
Write-Host "🏗️ Строим и запускаем контейнеры..." -ForegroundColor Yellow
docker-compose up --build -d

# Ждем, пока база данных будет готова
Write-Host "⏳ Ожидаем готовности базы данных..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Применяем миграции
Write-Host "📋 Применяем миграции..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py migrate

# Создаем тестовые данные (опционально)
Write-Host "📊 Создаем тестовые данные..." -ForegroundColor Yellow
try {
    docker-compose exec -T backend python manage.py loaddata test_data.json
} catch {
    Write-Host "⚠️ Тестовые данные не найдены, пропускаем" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Аниме-платформа успешно запущена!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Документация: http://localhost:8000/api/docs/" -ForegroundColor Cyan
Write-Host "⚙️ Админ-панель: http://localhost:8000/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Поиск аниме: http://localhost:3000/search" -ForegroundColor Magenta
Write-Host "📺 Список аниме: http://localhost:3000/anime" -ForegroundColor Magenta
Write-Host ""
Write-Host "📊 Статус сервисов:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🔍 Для просмотра логов: docker-compose logs -f" -ForegroundColor White
Write-Host "🛑 Для остановки: docker-compose down" -ForegroundColor White
Write-Host "🔄 Для перезапуска: docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "✨ Готово к использованию!" -ForegroundColor Green