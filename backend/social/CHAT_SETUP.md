# Настройка системы чатов

## Выполнить на сервере

### 1. Миграции

```bash
cd backend

# Создать миграции для новых моделей
python manage.py makemigrations social

# Применить миграции
python manage.py migrate social
```

### 2. Создать предустановленные обои (опционально)

```bash
python manage.py seed_chat_wallpapers
```

### 3. Перезапустить сервисы

```bash
# Перезапуск Celery для новых задач
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

# Перезапуск Daphne для WebSocket
sudo systemctl restart daphne

# Перезапуск Nginx (если нужно)
sudo systemctl restart nginx
```

### 4. Добавить задачи в Celery Beat (опционально)

Добавить в `celerybeat-schedule` или через Django Admin:

```python
# Очистка старых сообщений (ежедневно)
'cleanup-messages': {
    'task': 'social.tasks.cleanup_messages',
    'schedule': crontab(hour=3, minute=0),
    'args': (30,)  # дней
},

# Очистка истёкших блокировок (ежечасно)
'cleanup-expired-bans': {
    'task': 'social.tasks.cleanup_expired_bans',
    'schedule': crontab(minute=0),
},

# Очистка истёкших приглашений (ежечасно)
'cleanup-old-invites': {
    'task': 'social.tasks.cleanup_old_invites',
    'schedule': crontab(minute=0),
},

# Обновление статистики чатов (каждые 5 минут)
'update-chat-statistics': {
    'task': 'social.tasks.update_chat_statistics',
    'schedule': 300,  # секунд
},

# Обработка запланированных сообщений (каждую минуту)
'process-scheduled-messages': {
    'task': 'social.tasks.process_scheduled_messages',
    'schedule': 60,
},

# Обнаружение подозрительной активности (ежечасно)
'detect-suspicious-activity': {
    'task': 'social.tasks.detect_suspicious_activity',
    'schedule': crontab(minute=0),
},
```

## Новые API Endpoints

### Личные чаты
- `GET /api/social/private-chats/` - список чатов
- `POST /api/social/private-chats/` - создать чат
- `GET /api/social/private-chats/{id}/` - детали чата
- `DELETE /api/social/private-chats/{id}/` - удалить чат
- `GET /api/social/private-chats/{id}/messages/` - сообщения
- `POST /api/social/private-chats/{id}/messages/` - отправить сообщение
- `POST /api/social/private-chats/{id}/mark_as_read/` - пометить как прочитанное
- `POST /api/social/chats/{id}/clear-history/` - очистить историю
- `PUT /api/social/private-chats/{id}/settings/` - персональные настройки

### Групповые чаты
- `GET /api/social/group-chats/` - список групп
- `POST /api/social/group-chats/create/` - создать группу
- `GET /api/social/group-chats/{id}/` - детали группы
- `PATCH /api/social/group-chats/{id}/` - обновить группу
- `DELETE /api/social/group-chats/{id}/` - удалить группу
- `GET /api/social/group-chats/{id}/members/` - участники
- `POST /api/social/group-chats/{id}/invite_user/` - пригласить
- `POST /api/social/group-chats/{id}/remove_member/` - исключить
- `POST /api/social/group-chats/{id}/ban_user/` - забанить
- `POST /api/social/group-chats/{id}/unban_user/` - разбанить
- `POST /api/social/group-chats/{id}/leave_chat/` - покинуть группу
- `GET /api/social/group-chats/{id}/roles/` - роли
- `POST /api/social/group-chats/{id}/roles/` - создать роль
- `GET /api/social/group-chats/{id}/invite-links/` - ссылки-приглашения
- `POST /api/social/group-chats/{id}/invite-links/` - создать ссылку
- `GET /api/social/group-chats/{id}/admin-logs/` - журнал действий
- `GET /api/social/group-chats/{id}/banned-users/` - забаненные
- `GET /api/social/group-chats/{id}/restricted-users/` - ограниченные
- `GET /api/social/group-chats/{id}/analytics/` - аналитика

### Сообщения
- `GET /api/social/messages/{id}/` - детали сообщения
- `POST /api/social/messages/` - создать сообщение
- `PATCH /api/social/messages/{id}/` - редактировать
- `DELETE /api/social/messages/{id}/` - удалить
- `POST /api/social/messages/{id}/react/` - добавить реакцию
- `POST /api/social/messages/{id}/pin/` - закрепить
- `POST /api/social/messages/{id}/unpin/` - открепить
- `POST /api/social/messages/{id}/forward/` - переслать

### Папки чатов
- `GET /api/social/chat-folders/` - список папок
- `POST /api/social/chat-folders/` - создать папку
- `PATCH /api/social/chat-folders/{id}/` - обновить папку
- `DELETE /api/social/chat-folders/{id}/` - удалить папку
- `POST /api/social/chat-folders/reorder/` - изменить порядок
- `GET /api/social/chat-folders/{id}/chats/` - чаты в папке

### Кастомизация
- `GET /api/social/chat-wallpapers/` - доступные обои
- `POST /api/social/chat-wallpapers/` - загрузить обои
- `PUT /api/social/chats/{id}/wallpaper/` - установить обои
- `GET /api/social/chat-themes/` - доступные темы
- `PUT /api/social/chats/{id}/theme/` - установить тему

### Ссылки-приглашения
- `GET /api/social/chat-invite-links/` - список ссылок
- `POST /api/social/chat-invite-links/` - создать ссылку
- `DELETE /api/social/chat-invite-links/{id}/` - отозвать ссылку
- `POST /api/social/invite-links/join/{token}/` - присоединиться по ссылке

### Массовые операции
- `POST /api/social/group-chats/{id}/messages/bulk-delete/` - массовое удаление сообщений
- `POST /api/social/group-chats/{id}/members/bulk-add/` - массовое добавление участников
- `POST /api/social/group-chats/{id}/members/bulk-remove/` - массовое удаление участников

### Экспорт/Импорт
- `GET /api/social/chat-settings/export/` - экспорт настроек
- `POST /api/social/chat-settings/import/` - импорт настроек

### Журнал безопасности
- `GET /api/social/security-logs/` - журнал безопасности

## WebSocket события

### Подключение
```javascript
ws://domain/ws/chat/{chat_id}/?token={jwt_token}
ws://domain/ws/events/?token={jwt_token}
```

### События
- `new_message` - новое сообщение
- `message_edited` - сообщение отредактировано
- `message_deleted` - сообщение удалено
- `messages_read` - сообщения прочитаны
- `reaction_added` - реакция добавлена
- `reaction_removed` - реакция удалена
- `user_typing` - пользователь печатает
- `user_online` - пользователь онлайн/офлайн
- `user_joined` - пользователь присоединился
- `user_left` - пользователь покинул чат
- `chat_updated` - настройки чата изменены
- `role_changed` - роль изменена
- `settings_changed` - настройки изменены

## Использование сервисов

### PermissionChecker
```python
from social.services.chat_services import PermissionChecker

checker = PermissionChecker(user, chat)
if checker.has_permission('can_delete_messages').allowed:
    # Удаляем сообщение
    pass
```

### AntiSpamService
```python
from social.services.chat_services import AntiSpamService

anti_spam = AntiSpamService(chat)
result = anti_spam.check_message(message)
if result['is_spam']:
    anti_spam.apply_action(message, result['action'], result['action_duration'])
```

### RateLimiter
```python
from social.services.chat_services import rate_limiter

if rate_limiter.is_allowed(user_id, 'message', limit=10, period=60):
    # Разрешено
    pass
else:
    # Превышен лимит
    retry_after = rate_limiter.get_retry_after(user_id, 'message')
```

### ChatAnalytics
```python
from social.services.chat_services import ChatAnalytics

analytics = ChatAnalytics(chat)
stats = analytics.get_activity_stats(days=7)
score = analytics.get_engagement_score()
```

## Структура файлов

```
social/
├── models.py              # Основные модели
├── models_chat.py         # Дополнительные модели чатов
├── serializers.py         # Основные сериализаторы
├── serializers_chat.py    # Сериализаторы чатов
├── views.py               # Основные views
├── views_chat.py          # Views чатов
├── urls.py                # Маршруты
├── consumers.py           # WebSocket consumers
├── tasks.py               # Celery задачи
├── permissions.py         # Permissions
├── services/
│   ├── __init__.py
│   └── chat_services.py   # Сервисы чатов
└── migrations/
    └── ...                # Миграции
```

## Переменные окружения

Убедитесь, что в `.env` указаны:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```
