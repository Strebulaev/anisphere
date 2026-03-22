# KODA.md — Инструкции для работы с проектом AnimeCore

## Обзор проекта

**AnimeCore** — это социальная сеть для анимешников, объединяющая поиск аниме, создание плейлистов, озвучки и сообщество. Платформа предназначена для русскоязычных анимешников и включает в себя функционал для просмотра аниме, управления коллекциями, взаимодействия с группами озвучек и социальными функциями.

## Технологический стек

### Backend
- **Django 4.2.10** — основной веб-фреймворк
- **Django REST Framework** — REST API
- **PostgreSQL 15** — основная база данных
- **Redis 7** — кэширование и сессии
- **Celery + RabbitMQ** — фоновая обработка задач
- **MinIO** — S3-совместимое хранилище для медиафайлов
- **Gunicorn + Nginx** — продакшен-сервер

### Frontend
- **Vue.js 3** — JavaScript-фреймворк
- **TypeScript** — типизация
- **Tailwind CSS** — стилизация
- **Pinia** — управление состоянием
- **Vue Router 4** — маршрутизация
- **Axios** — HTTP-клиент
- **HLS.js / Video.js** — видеоплеер

### Инфраструктура
- **Docker + Docker Compose** — контейнеризация
- **Vercel** — деплой фронтенда
- **VPS Hetzner/Timeweb** — хостинг бэкенда

---

## Структура проекта

```
animecore/
├── backend/                 # Django-приложение
│   ├── anime/              # Приложение аниме (модели, views, serializers)
│   ├── users/              # Приложение пользователей
│   ├── social/             # Социальные функции (группы, комментарии)
│   ├── playlists/          # Плейлисты
│   ├── dubs/               # Озвучки и студии
│   ├── reactor/            # Shorts-видео
│   ├── notifications/      # Уведомления
│   ├── parsers/            # Парсеры аниме
│   ├── config/             # Конфигурация
│   ├── manage.py           # Django CLI
│   ├── requirements.txt    # Python-зависимости
│   └── docker-compose.yml  # Docker-конфигурация
│
├── frontend/               # Vue.js-приложение
│   ├── src/
│   │   ├── api/           # API-клиенты
│   │   ├── components/    # Vue-компоненты
│   │   ├── views/         # Страницы
│   │   ├── stores/        # Pinia-сторе
│   │   ├── router/        # Маршрутизация
│   │   └── types/         # TypeScript-типы
│   ├── package.json       # Node.js-зависимости
│   └── vite.config.ts     # Vite-конфигурация
│
├── docker-compose.yml      # Основная Docker-конфигурация
├── README.md              # Документация проекта
└── KODA.md                # Этот файл
```

---

## Установка и запуск

### Требования
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (или использовать Docker)

### Быстрый старт через Docker

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/animecore.git
cd animecore

# Запуск через Docker Compose
docker-compose up -d
```

### Ручной запуск Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
```

### Ручной запуск Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Сборка для продакшена
npm run build
```

---

## Основные команды

### Django (Backend)

```bash
# Миграции
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Загрузка фикстур
python manage.py loaddata fixtures.json

# Запуск shell
python manage.py shell

# Сбор статики
python manage.py collectstatic
```

### Vue.js (Frontend)

```bash
# Dev-сервер
npm run dev

# Сборка
npm run build

# Предпросмотр сборки
npm run preview

# Проверка типов TypeScript
npm run type-check

# Линтинг
npm run lint

# Unit-тесты
npm run test:unit
```

### Docker

```bash
# Сборка и запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f backend

# Пересборка
docker-compose build --no-cache
```

---

## API Endpoints

### Аутентификация
```
POST /api/auth/login/       # Вход
POST /api/auth/register/    # Регистрация
POST /api/auth/refresh/     # Обновление токена
GET  /api/auth/user/        # Текущий пользователь
```

### Аниме
```
GET  /api/anime/            # Список аниме с фильтрами
GET  /api/anime/{id}/       # Детали аниме
GET  /api/anime/{id}/episodes/      # Эпизоды
GET  /api/anime/{id}/translations/  # Переводы
GET  /api/anime/{id}/kodik_player/  # Ссылка на Kodik плеер
```

### Поиск
```
GET /api/anime/search/?q=запрос    # Поиск аниме
GET /api/anime/updates/            # Последние обновления
```

### Плейлисты
```
GET    /api/playlists/             # Список плейлистов
POST   /api/playlists/             # Создание плейлиста
GET    /api/playlists/{id}/        # Детали плейлиста
PUT    /api/playlists/{id}/        # Обновление плейлиста
DELETE /api/playlists/{id}/        # Удаление плейлиста
POST   /api/playlists/{id}/add_item/   # Добавление аниме
```

### Озвучки
```
GET /api/dubs/                     # Список групп озвучек
GET /api/dubs/{id}/                # Детали группы
```

### Социальные функции
```
GET  /api/social/comments/         # Комментарии
POST /api/social/comments/         # Создание комментария
GET  /api/social/groups/           # Список групп
POST /api/social/groups/           # Создание группы
```

### Reactor (Shorts)
```
GET  /api/reactor/posts/           # Список видео
POST /api/reactor/posts/           # Загрузка видео
POST /api/reactor/posts/{id}/like/ # Лайк
```

### Модерация
```
GET  /api/notifications/complaints/    # Жалобы
POST /api/notifications/complaints/    # Создание жалобы
GET  /api/notifications/               # Уведомления
```

---

## Модели данных

### Основные модели (Backend)

#### Anime
Модель аниме с основной информацией:
- `title_ru`, `title_en`, `title_jp` — названия на разных языках
- `shikimori_id` — ID на Shikimori
- `status` — статус (ongoing, finished, announced, canceled)
- `kind` — тип (tv, movie, ova, special, ona, music)
- `episodes` — количество эпизодов
- `score` — рейтинг
- `poster_url`, `poster` — постер
- `genres`, `studios` — JSON-поля для жанров и студий
- `kodik_link`, `kodik_id` — интеграция с Kodik

#### Playlist / PlaylistItem
Плейлисты пользователей с элементами

#### DubStudio
Студия озвучки (AniMedia, AniLibria, SHIZA Project и др.)

#### VoiceActor
Актер озвучки

#### Dub
Озвучка конкретного аниме студией

#### VideoSource
Источник видео для аниме (Kodik, Aniboom, Jutsu)

#### Translation
Перевод/озвучка для аниме

#### WatchProgress
Прогресс просмотра пользователя

#### Genre, Studio
Справочники жанров и студий

---

## Переменные окружения

### Backend (.env)
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/animecore
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret

# Email
EMAIL_HOST=smtp.yandex.ru
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password

# Kodik API
KODIK_API_TOKEN=your-kodik-token
```

---

## Скрипты импорта аниме

В проекте есть множество скриптов для импорта данных из внешних источников:

- `import_anime_universal.py` — универсальный импорт
- `import_shikimori_full.py` — импорт из Shikimori
- `import_jikan_full.py` — импорт из Jikan API
- `full_import_with_images.py` — импорт с изображениями
- `auto_shikimori_import.py` — автоматический импорт из Shikimori

Запуск:
```bash
cd backend
python import_shikimori_full.py
```

---

## Правила разработки

### Стиль кода (Backend)
- Используется Django-стиль (snake_case для переменных, PascalCase для классов)
- Обязательное использование DRF serializers для API
- ViewSets для стандартных CRUD-операций
- Кастомные actions для дополнительных endpoints
- Типизация с использованием type hints

### Стиль кода (Frontend)
- Vue.js 3 Composition API
- TypeScript для всех компонентов
- Tailwind CSS для стилизации
- Pinia для управления состоянием
- Компоненты именуются в PascalCase (например, `AnimeCard.vue`)
- Сторы именуются в snake_case (например, `anime.ts`)

    1. ОБЩИЕ ПРАВИЛА
    1.1 Полнота реализации
    Никаких заглушек. Каждая функция должна быть полностью реализована.

    Никаких TODO-комментариев в коде, который попадает в продакшен.

    Никаких console.log, print, alert в финальном коде.

    Каждый API endpoint должен возвращать реальные данные из базы, а не мок-данные.

    Каждая кнопка должна выполнять реальное действие, а не показывать alert.

    1.2 Обработка ошибок
    Все API-запросы должны иметь обработку ошибок на фронтенде и бэкенде.

    На фронтенде: показывать понятные пользователю сообщения об ошибках.

    На бэкенде: возвращать соответствующие HTTP-статусы и информативные сообщения.

    Логировать ошибки в Sentry или аналогичную систему.

    1.3 Валидация данных
    Все входные данные должны валидироваться на бэкенде.

    На фронтенде должна быть базовая валидация перед отправкой.

    SQL-инъекции и XSS должны быть предотвращены на всех уровнях.

    2. ПРАВИЛА ДЛЯ БЭКЕНДА
    2.1 Структура кода
    Каждое приложение Django должно иметь четкое разделение: models.py, serializers.py, views.py, urls.py.

    Бизнес-логика должна выноситься в services.py или utils.py, а не храниться во views.

    Повторно используемые функции выносить в отдельные модули.

    2.2 Модели
    Все модели должны иметь Meta-класс с ordering и indexes для часто запрашиваемых полей.

    Использовать UUID вместо автоинкрементных ID для всех моделей.

    Добавлять поля created_at и updated_at во все модели.

    Использовать ForeignKey с related_name для обратных связей.

    Для полей с выбором использовать Enum-классы.

    2.3 API
    Все API должно быть задокументировано (можно через drf-yasg или аналоги).

    Использовать ViewSets для стандартных CRUD-операций.

    Для кастомных действий использовать @action декоратор.

    Пагинация должна быть реализована для всех списковых эндпоинтов.

    Фильтрация должна поддерживать множественный выбор, диапазоны и поиск.

    2.4 База данных
    Все запросы должны быть оптимизированы (использовать select_related, prefetch_related).

    Избегать N+1 запросов.

    Для сложных фильтров использовать Django Filters.

    Индексировать поля, по которым часто идет поиск и сортировка.

    2.5 Аутентификация и авторизация
    Использовать JWT для API.

    Проверять права доступа в каждом эндпоинте.

    Разделять права для разных ролей (пользователь, модератор, админ).

    3. ПРАВИЛА ДЛЯ ФРОНТЕНДА
    3.1 Компоненты
    Каждый компонент должен быть переиспользуемым, если это возможно.

    Компоненты должны принимать пропсы с валидацией типов (TypeScript).

    Логика должна быть вынесена в composables, а не храниться в компонентах.

    Стили должны быть scoped или использовать модули CSS.

    3.2 Состояние (Pinia)
    Сторы должны быть разделены по функциональным областям (auth, anime, playlist).

    В сторах должна быть обработка ошибок и состояний загрузки.

    Не хранить в сторе то, что можно получить из API при каждом запросе.

    Использовать геттеры для вычисляемых значений.

    3.3 API-запросы (Axios)
    Все API-запросы должны проходить через единый экземпляр axios с настроенными интерцепторами.

    Интерцепторы должны автоматически добавлять токен авторизации.

    Интерцепторы должны обрабатывать ошибки (401 — редирект на логин, 500 — показ сообщения).

    Использовать отдельные файлы для каждой группы эндпоинтов.

    3.4 Роутинг
    Все маршруты должны быть типизированы.

    Защищенные маршруты должны проверять авторизацию перед загрузкой.

    Использовать динамические импорты для lazy loading страниц.

    Обрабатывать 404 для несуществующих маршрутов.

    3.5 UI/UX
    Все интерактивные элементы должны иметь состояния (loading, disabled, active).

    Формы должны показывать ошибки валидации под каждым полем.

    Загрузка данных должна отображаться скелетонами, а не спиннерами где уместно.

    Пустые состояния должны предлагать действия (например, "Создать первый плейлист").

    Все действия должны иметь подтверждение для необратимых операций (удаление).

    4. ПРАВИЛА ДЛЯ КОНКРЕТНЫХ ФУНКЦИЙ
    4.1 Плейлисты
    При создании плейлиста обязательно проверять наличие хотя бы одного аниме.

    Поиск аниме при создании должен работать в реальном времени с debounce.

    Статусы ссылок должны обновляться автоматически или по жалобам.

    Плейлист по ссылке должен работать без авторизации (только просмотр).

    4.2 Коллекция пользователя
    Статус аниме должен обновляться автоматически при просмотре.

    Прогресс просмотра должен сохраняться и синхронизироваться между устройствами.

    При изменении статуса должны обновляться счетчики в профиле.

    4.3 Reactor (Shorts)
    Видео должны загружаться с прогресс-баром.

    После загрузки видео должно проходить модерацию перед публикацией.

    Лента должна работать с бесконечной прокруткой.

    Привязка к аниме обязательна для каждого видео.

    4.4 Чат
    Сообщения должны доставляться в реальном времени через WebSocket.

    История сообщений должна подгружаться по мере скролла.

    Непрочитанные сообщения должны отображаться в списке чатов.

    Прикрепленные файлы должны иметь предпросмотр.

    4.5 Конкурсы
    Подача работ должна проверять соответствие формату и размеру.

    Голосование должно быть защищено от накруток.

    Результаты должны объявляться автоматически по окончании.

    Призы должны отмечаться как врученные с подтверждением.



### Тестирование
- Backend: Django TestCase
- Frontend: Vitest + Vue Test Utils
- Запуск тестов: `npm run test:unit`

### Линтинг
- Backend: flake8, isort
- Frontend: ESLint + Prettier
- Команда линтинга: `npm run lint`

---

## Часто встречающиеся задачи

### Добавление нового API endpoint
1. Создать serializer в `serializers.py`
2. Добавить view/viewset в `views.py`
3. Настроить URL в `urls.py`

### Добавление новой модели
1. Создать модель в `models.py`
2. Создать serializer
3. Создать view/viewset
4. Добавить URL
5. Создать миграцию: `python manage.py makemigrations`
6. Применить миграцию: `python manage.py migrate`

### Добавление новой страницы на Frontend
1. Создать компонент в `src/views/`
2. Добавить маршрут в `src/router/`
3. Добавить ссылку в навигацию

---

## Полезные ссылки

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Vue.js 3 Documentation](https://vuejs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Kodik API](https://kodik.cc/)

---

## Контакты

- Email: contact@animecore.app
- Telegram: @animecore_support
- Discord: AnimeCore Community
