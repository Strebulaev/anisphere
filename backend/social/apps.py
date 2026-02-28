from django.apps import AppConfig


class SocialConfig(AppConfig):
    name = 'social'

    def ready(self):
        # Импортируем сигналы для автоматического создания системных постов
        import social.signals  # noqa
