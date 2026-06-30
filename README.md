# Anisphere

Аниме-портал с каталогом, плейлистами, коллекциями и социальными функциями.

---

## Требования

- **Node.js** 20.19.0+ или 22.12.0+
- **Python** 3.10+
- **Docker** и **Docker Compose**
---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone anisphere
cd anisphere
```

### 2. Настройка Backend

```bash
cd backend
copy .env.example .env
```

Отредактируйте `.env` и укажите:
- `SECRET_KEY`
- `DEBUG=True`
- `DATABASE_URL`
- `KODIK_TOKEN` (почта kodik support@kodikres.com)

### 3. Запуск Backend

```bash
cd backend
docker-compose up -d --build
docker exec anisphere_backend python manage.py migrate
docker exec -it anisphere_backend python manage.py createsuperuser
```

Backend доступен: `http://localhost:8000`

### 4. Настройка Frontend

```bash
cd frontend
npm install
copy .env.example .env
```

### 5. Запуск Frontend

```bash
cd frontend
npm run dev
```

Frontend доступен: `http://localhost:5173`

---

## Импорт данных

### Импорт аниме из Kodik

```bash
cd backend
docker exec anisphere_backend python kodik_import.py
```

**Опции:**
```bash
# Тестовый импорт (25 записей)
docker exec anisphere_backend python kodik_import.py --limit 25

# С обновлением существующих
docker exec anisphere_backend python kodik_import.py --replace

# Исправление количества эпизодов
docker exec anisphere_backend python kodik_import.py --fix-episodes
```

### Скачивание постеров

```bash
docker exec -it anisphere_backend python manage.py shell < download_all_posters.py
```

### Создание франшиз из JSON

```bash
cd backend
python manage.py create_franchises_from_json franshize_anime.json
```

---

## Управление базой данных

```bash
# Миграции
docker exec anisphere_backend python manage.py migrate
docker exec anisphere_backend python manage.py makemigrations

# Дамп данных
docker exec anisphere_backend python manage.py dumpdata > backup.json

# Загрузка данных
docker exec anisphere_backend python manage.py loaddata backup.json
```

---

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/anime/` | Список аниме |
| GET | `/api/anime/{id}/` | Детали аниме |
| GET | `/api/anime/search/` | Поиск аниме |
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| GET | `/api/playlists/` | Плейлисты пользователя |
| POST | `/api/playlists/` | Создать плейлист |

---

## Разработка

### Frontend

```bash
cd frontend
npm run dev      # Dev-сервер
npm run lint     # Линтинг
npm run format   # Форматирование
npm run test     # Тесты
```

### Backend

```bash
cd backend
docker-compose up -d      # Запуск
docker-compose logs -f    # Логи
docker-compose down       # Остановка
docker-compose restart    # Перезапуск
```

---

## Переменные окружения

### Backend (.env)

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@db:5432/anisphere
KODIK_TOKEN=kodik-token
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
VITE_KODIK_TOKEN=kodik-token
```

---

## Полезные команды

```bash
# Очистка кэша Django
docker exec anisphere_backend python manage.py clearcache

# Сборка статики
docker exec anisphere_backend python manage.py collectstatic

# Проверка миграций
docker exec anisphere_backend python manage.py showmigrations

# Перезапуск сервисов
docker-compose restart
```

---

## Устранение проблем

### Backend не запускается

```bash
docker-compose logs backend
docker-compose up -d --build --force-recreate
```

### Frontend не подключается к API

Проверьте `VITE_API_URL` в `.env` и CORS настройки в backend.

### Ошибки базы данных

```bash
docker exec anisphere_backend python manage.py migrate --fake <app> zero
docker exec anisphere_backend python manage.py migrate
```
