from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        # Импортируем сигналы при запуске приложения
        import users.signals

