# Система Чатов - Документация

## Обзор

Система чатов была расширена новыми функциями согласно архитектурной документации.

## Новые модели данных

### 1. ChatInvite (Приглашения в чаты)
- **Поля:**
  - `token` - уникальный токен приглашения
  - `expires_at` - дата истечения
  - `max_uses` - максимальное количество использований
  - `uses_count` - количество использований
  - `is_active` - активность приглашения

### 2. Reaction (Реакции на сообщения)
- **Поля:**
  - `message` - сообщение
  - `user` - пользователь
  - `emoji` - эмодзи реакции
- **Уникальность:** message + user + emoji

### 3. Attachment (Вложения)
- **Поля:**
  - `type` - тип (image, video, audio, file)
  - `file` - файл
  - `file_name` - имя файла
  - `file_size` - размер в байтах
  - `mime_type` - MIME-тип
  - `thumbnail` - миниатюра
  - `width`, `height` - размеры (для изображений/видео)
  - `duration` - длительность (для аудио/видео)

### 4. EmailLog (Лог email-уведомлений)
- **Поля:**
  - `user` - пользователь
  - `email_type` - тип (daily_digest, weekly_digest, mention, message, system, chat_invite)
  - `subject` - тема письма
  - `to_email` - email получателя
  - `content` - HTML-контент
  - `status` - статус (pending, sent, failed)
  - `sent_at` - время отправки
  - `error_message` - сообщение об ошибке

## Расширенные модели

### GroupChat
- Добавлено поле `anime` - связь с аниме

### Message
- Добавлены поля:
  - `is_pinned` - закреплено ли сообщение
  - `pinned_by` - кто закрепил
  - `pinned_at` - время закрепления
  - `forwarded_from` - переслано из сообщения

## Redis Кэширование

### ChatCacheService

Сервис для работы с кэшем чатов в Redis.

#### Методы:

**Последние сообщения:**
- `get_last_messages(chat_id, limit=50)` - получить последние сообщения
- `add_message_to_cache(chat_id, message, max_cached=50)` - добавить сообщение в кэш
- `update_message_in_cache(chat_id, message_id, updates)` - обновить сообщение в кэше
- `remove_message_from_cache(chat_id, message_id)` - удалить сообщение из кэша
- `get_last_message(chat_id)` - получить последнее сообщение
- `set_last_message(chat_id, message)` - установить последнее сообщение

**Информация о чатах:**
- `set_chat_info(chat_id, info)` - сохранить информацию о чате
- `get_chat_info(chat_id)` - получить информацию о чате
- `invalidate_chat_info(chat_id)` - инвалидировать кэш чата

**Информация о пользователях:**
- `set_user_info(user_id, info)` - сохранить информацию о пользователе
- `get_user_info(user_id)` - получить информацию о пользователе
- `invalidate_user_info(user_id)` - инвалидировать кэш пользователя

**Непрочитанные сообщения:**
- `increment_unread(user_id, chat_id, count=1)` - увеличить счётчик
- `decrement_unread(user_id, chat_id, count=1)` - уменьшить счётчик
- `get_unread_count(user_id, chat_id=None)` - получить количество
- `get_unread_chats(user_id)` - получить список чатов с непрочитанными
- `mark_chat_read(user_id, chat_id)` - отметить чат прочитанным

**Статус печати:**
- `set_typing(chat_id, user_id)` - установить статус печати
- `remove_typing(chat_id, user_id)` - удалить статус печати
- `get_typing_users(chat_id, user_ids)` - получить печатающих пользователей

**Очистка кэша:**
- `clear_chat_cache(chat_id)` - очистить кэш чата
- `clear_user_cache(user_id)` - очистить кэш пользователя

## API Endpoints

### Приглашения в чаты

```
GET    /api/social/chat-invites/                 - Список приглашений
POST   /api/social/chat-invites/                 - Создать приглашение
GET    /api/social/chat-invites/{id}/            - Детали приглашения
PUT    /api/social/chat-invites/{id}/            - Обновить приглашение
DELETE /api/social/chat-invites/{id}/            - Удалить приглашение
POST   /api/social/chat-invites/{id}/regenerate/ - Пересоздать токен
POST   /api/social/chat-invites/{id}/revoke/     - Отозвать приглашение
POST   /api/social/chat-invites/join/{token}/    - Присоединиться по токену
```

### Реакции

```
GET    /api/social/reactions/              - Список реакций
POST   /api/social/reactions/              - Создать реакцию (toggle)
GET    /api/social/reactions/for_message/  - Реакции на сообщение
POST   /api/social/messages/{id}/reaction/toggle/ - Переключить реакцию
```

### Вложения

```
GET    /api/social/attachments/                    - Список вложений
POST   /api/social/attachments/                    - Загрузить вложение
GET    /api/social/attachments/{id}/               - Детали вложения
PUT    /api/social/attachments/{id}/               - Обновить вложение
DELETE /api/social/attachments/{id}/               - Удалить вложение
POST   /api/social/messages/{id}/attachments/upload/ - Загрузить вложение к сообщению
```

### Действия с сообщениями

```
POST /api/social/messages/{id}/pin/           - Закрепить сообщение
POST /api/social/messages/{id}/unpin/         - Открепить сообщение
POST /api/social/messages/{id}/forward/       - Переслать сообщение
GET  /api/social/chats/{id}/pinned-messages/  - Закреплённые сообщения
```

### Непрочитанные сообщения

```
GET /api/social/chats/unread-count/       - Количество непрочитанных
GET /api/social/chats/unread/             - Чаты с непрочитанными
POST /api/social/chats/{id}/mark-read/    - Отметить чат прочитанным
```

### Email логи

```
GET    /api/social/email-logs/           - Список логов
POST   /api/social/email-logs/           - Создать лог
GET    /api/social/email-logs/stats/     - Статистика уведомлений
```

### Поиск

```
GET /api/social/messages/search/  - Поиск по сообщениям
POST /api/social/messages/reindex/ - Переиндексация (админ)
```

## Фоновые задачи (Celery)

### Задачи:

1. **send_push_notification** - Отправить push-уведомление
2. **send_email_digest** - Отправить email-дайджест (daily/weekly)
3. **send_mention_notification** - Уведомление об упоминании
4. **cleanup_old_messages** - Очистка старых сообщений (ежедневно)
5. **cleanup_unused_attachments** - Очистка неиспользуемых вложений
6. **cleanup_expired_invites** - Очистка просроченных приглашений
7. **generate_thumbnail_for_attachment** - Генерация миниатюры
8. **send_chat_invite_notification** - Уведомление о приглашении
9. **index_message_for_search** - Индексация для поиска
10. **archive_old_chats** - Архивация неактивных чатов
11. **process_new_message** - Обработка нового сообщения (уведомления, индексация)

## Поиск (Elasticsearch)

### MessageDocument

Документ для индексации сообщений в Elasticsearch.

**Поля:**
- `id`
- `text`
- `media_type`
- `created_at`
- `updated_at`
- `sender_id`
- `sender_username`
- `chat_id`
- `chat_name`
- `private_chat_id`

### search_messages()

Функция поиска с параметрами:
- `query` - поисковый запрос
- `user_id` - ID пользователя (для фильтрации по доступу)
- `chat_id` - ID чата (опционально)
- `media_type` - тип медиа (опционально)
- `date_from` - начальная дата (опционально)
- `date_to` - конечная дата (опционально)

## WebSocket события

### Новые события:

```javascript
{
  "action": "new_message",
  "message": { ... }  // Полные данные сообщения с реакциями и вложениями
}

{
  "action": "message_updated",
  "message": { ... }  // Обновлённое сообщение
}

{
  "action": "message_deleted",
  "message_id": 123
}

{
  "action": "message_pinned",
  "message": { ... }
}

{
  "action": "message_unpinned",
  "message_id": 123
}

{
  "action": "reaction_added",
  "message_id": 123,
  "emoji": "❤️",
  "user": { ... }
}

{
  "action": "reaction_removed",
  "message_id": 123,
  "emoji": "❤️",
  "user_id": 456
}
```

## Интеграция с другими модулями

### Связь с аниме
- GroupChat может быть привязан к аниме через поле `anime`
- Чаты отображаются на странице аниме
- Можно отправлять карточки аниме в чат

### Связь с плейлистами
- Можно отправлять карточки плейлистов в чат

### Связь с Reactor
- Можно отправлять shorts в чат

## Ограничения

| Сущность | Бесплатно | Премиум |
|----------|-----------|---------|
| Размер сообщения | 4000 символов | 10000 символов |
| Размер файла | 10 МБ | 50 МБ |
| Участников в группе | 100 | 500 |
| Закреплённых сообщений | 5 | 20 |
| Хранение истории | 30 дней | 1 год |
| Частота сообщений | 10/мин | 30/мин |

## Безопасность

1. **Шифрование:** Все сообщения по HTTPS/WSS
2. **Rate limiting:** Ограничение на отправку сообщений
3. **Модерация:** Возможность пожаловаться на сообщение
4. **Валидация:** Проверка размера файлов, типа контента

## Миграции

Для применения изменений:

```bash
python manage.py makemigrations social
python manage.py migrate social
```

## Требуемые зависимости

Для Elasticsearch:
```bash
pip install django-elasticsearch-dsl
```

Для Celery (уже установлен):
```bash
pip install celery redis
```

## Настройка

### Redis кэширование

Убедитесь, что Redis настроен в settings.py:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Celery

Настройка в config/celery.py уже существует.

### Elasticsearch

Настройка в settings.py:

```python
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200',
    },
}
```

## Примеры использования

### Создание приглашения

```python
POST /api/social/chat-invites/
{
    "chat": 1,
    "expires_at": "2024-12-31T23:59:59Z",
    "max_uses": 10
}
```

### Переключение реакции

```python
POST /api/social/messages/123/reaction/toggle/
{
    "emoji": "❤️"
}
```

### Закрепление сообщения

```python
POST /api/social/messages/123/pin/
```

### Пересылка сообщения

```python
POST /api/social/messages/123/forward/
{
    "chat_id": 456
}
```

### Поиск сообщений

```python
GET /api/social/messages/search/?q=привет&media_type=text&date_from=2024-01-01
```

## Поддержка

Для вопросов и проблем обращайтесь к разработчикам.
