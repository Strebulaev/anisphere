import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Загружаем настройки из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях
app.autodiscover_tasks()

# Принудительно устанавливаем бэкенд
app.conf.update(
    result_backend='redis://localhost:6379/0',
    broker_url='redis://localhost:6379/0',
    result_extended=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=280,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')