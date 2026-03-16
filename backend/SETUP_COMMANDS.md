# Команды для запуска системы чатов

## Миграции

```bash
cd backend

# Создать миграции для новых моделей
python manage.py makemigrations social

# Применить миграции
python manage.py migrate social
```

## Перезапуск сервисов

```bash
# Перезапуск Celery worker
sudo systemctl restart celery-worker

# Перезапуск Celery beat (планировщик задач)
sudo systemctl restart celery-beat

# Перезапуск Daphne (WebSocket сервер)
sudo systemctl restart daphne

# Перезапуск Nginx
sudo systemctl restart nginx
```

## Проверка

```bash
# Проверить статус миграций
python manage.py showmigrations social

# Запустить Django shell для проверки моделей
python manage.py shell
```

В shell проверить импорт:
```python
from social.models_chat import ChatFolder, ChatFolderChat, SecurityLog, GroupChatSettings, PrivateChatSettings, MessagePin
from social.services.chat_services import PermissionChecker, AntiSpamService, ChatAnalytics
print("OK")
```

## Дополнительно

```bash
# Создать суперпользователя (если нужно)
python manage.py createsuperuser

# Собрать статику
python manage.py collectstatic --noinput
```
