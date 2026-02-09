#!/bin/bash

# AnimeCore - Скрипт быстрой установки и настройки с AnimeParsers
# Этот скрипт автоматически настроит проект для работы с аниме

set -e  # Остановка при ошибке

echo "🎌 AnimeCore - Установка и настройка с AnimeParsers"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Проверка Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не установлен. Установите Python 3.8+"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $python_version найден"
}

# Проверка Node.js
check_nodejs() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js не установлен. Frontend не будет настроен."
        FRONTEND_AVAILABLE=false
    else
        node_version=$(node --version)
        print_success "Node.js $node_version найден"
        FRONTEND_AVAILABLE=true
    fi
}

# Установка AnimeParsers
install_animeparsers() {
    print_info "Установка AnimeParsers..."
    
    if pip3 install anime-parsers-ru; then
        print_success "AnimeParsers установлен"
    else
        print_error "Ошибка установки AnimeParsers"
        exit 1
    fi
    
    # Устанавливаем дополнительные зависимости
    pip3 install anime-parsers-ru[async] || print_warning "Не удалось установить асинхронную версию"
}

# Настройка backend
setup_backend() {
    print_info "Настройка backend..."
    
    cd backend
    
    # Создание виртуального окружения если не существует
    if [ ! -d "venv" ]; then
        print_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Установка зависимостей
    if [ -f "requirements.txt" ]; then
        print_info "Установка зависимостей из requirements.txt..."
        pip install -r requirements.txt
    else
        print_info "Установка базовых зависимостей..."
        pip install django djangorestframework django-filter
    fi
    
    # Установка AnimeParsers в виртуальное окружение
    pip install anime-parsers-ru
    
    # Настройка базы данных
    print_info "Настройка базы данных..."
    python manage.py makemigrations
    python manage.py migrate
    
    print_success "Backend настроен"
    cd ..
}

# Настройка frontend
setup_frontend() {
    if [ "$FRONTEND_AVAILABLE" = false ]; then
        return
    fi
    
    print_info "Настройка frontend..."
    
    cd frontend
    
    # Установка зависимостей
    if [ -f "package.json" ]; then
        print_info "Установка npm зависимостей..."
        npm install
    else
        print_warning "package.json не найден. Пропускаем настройку frontend."
        cd ..
        return
    fi
    
    print_success "Frontend настроен"
    cd ..
}

# Импорт тестовых данных
import_test_data() {
    print_info "Импорт тестовых данных..."
    
    cd backend
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Импорт из Shikimori (безопасно)
    echo "Импорт аниме из Shikimori..."
    python manage.py import_animeparsers --source shikimori
    
    print_success "Тестовые данные импортированы"
    cd ..
}

# Запуск тестов
run_tests() {
    print_info "Запуск тестов..."
    
    cd backend
    source venv/bin/activate
    
    if python test_animeparsers.py; then
        print_success "Все тесты прошли успешно!"
    else
        print_warning "Некоторые тесты не прошли. Проверьте настройки."
    fi
    
    cd ..
}

# Создание скриптов запуска
create_startup_scripts() {
    print_info "Создание скриптов запуска..."
    
    # Скрипт запуска backend
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
python manage.py runserver
EOF
    
    # Скрипт запуска frontend
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
    
    # Скрипт полного запуска
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "🚀 Запуск AnimeCore..."

# Запуск backend в фоне
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
cd ..

# Ожидание запуска backend
sleep 3

# Запуск frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ AnimeCore запущен!"
echo "🔗 Backend: http://localhost:8000"
echo "🎌 Frontend: http://localhost:3000"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Обработка сигнала завершения
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Ожидание
wait
EOF
    
    # Делаем скрипты исполняемыми
    chmod +x start_*.sh
    
    print_success "Скрипты запуска созданы"
}

# Главное меню
show_menu() {
    echo ""
    echo "🎯 Выберите действие:"
    echo "1) Полная установка (рекомендуется)"
    echo "2) Только установка зависимостей"
    echo "3) Только настройка backend"
    echo "4) Только настройка frontend"
    echo "5) Импорт тестовых данных"
    echo "6) Запуск тестов"
    echo "7) Создать скрипты запуска"
    echo "8) Выход"
    echo ""
}

# Полная установка
full_install() {
    print_info "Начинаем полную установку..."
    
    check_python
    check_nodejs
    install_animeparsers
    setup_backend
    setup_frontend
    import_test_data
    create_startup_scripts
    run_tests
    
    print_success "🎉 Установка завершена!"
    echo ""
    echo "💡 Следующие шаги:"
    echo "   ./start_all.sh           - Запустить все сервисы"
    echo "   ./start_backend.sh      - Только backend"
    echo "   ./start_frontend.sh     - Только frontend"
    echo ""
    echo "🔗 URL после запуска:"
    echo "   Backend API:  http://localhost:8000"
    echo "   Frontend:     http://localhost:3000"
}

# Обработка аргументов командной строки
case "${1:-}" in
    --full|--install)
        full_install
        ;;
    --deps)
        install_animeparsers
        ;;
    --backend)
        setup_backend
        ;;
    --frontend)
        setup_frontend
        ;;
    --import)
        import_test_data
        ;;
    --test)
        run_tests
        ;;
    --scripts)
        create_startup_scripts
        ;;
    --help|-h)
        echo "AnimeCore - Скрипт установки"
        echo ""
        echo "Использование: $0 [опция]"
        echo ""
        echo "Опции:"
        echo "  --full, --install    Полная установка (по умолчанию)"
        echo "  --deps              Только установка зависимостей"
        echo "  --backend           Только настройка backend"
        echo "  --frontend          Только настройка frontend"
        echo "  --import            Импорт тестовых данных"
        echo "  --test              Запуск тестов"
        echo "  --scripts           Создать скрипты запуска"
        echo "  --help, -h          Показать эту справку"
        echo ""
        exit 0
        ;;
    "")
        # Интерактивный режим
        while true; do
            show_menu
            read -p "Выберите опцию (1-8): " choice
            
            case $choice in
                1) full_install; break ;;
                2) install_animeparsers ;;
                3) setup_backend ;;
                4) setup_frontend ;;
                5) import_test_data ;;
                6) run_tests ;;
                7) create_startup_scripts ;;
                8) print_info "До свидания!"; exit 0 ;;
                *) print_error "Неверный выбор. Попробуйте снова." ;;
            esac
        done
        ;;
    *)
        print_error "Неизвестная опция: $1"
        echo "Используйте $0 --help для справки"
        exit 1
        ;;
esac