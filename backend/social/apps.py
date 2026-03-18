from django.apps import AppConfig


class SocialConfig(AppConfig):
    name = 'social'

    def ready(self):
        import social.signals       # noqa — сигналы ленты
        import social.signals_chat  # noqa — сигналы чатов (кэш, счётчики)
