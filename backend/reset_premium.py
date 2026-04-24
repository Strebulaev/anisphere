"""
Скрипт сброса премиум подписок для всех пользователей.
"""

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import Subscription
from django.db import transaction


def reset_all_premium():
    """Сбрасывает премиум для всех пользователей."""
    print("🔄 Сброс премиум подписок...")

    # Сбрасываем Subscription
    subscriptions = Subscription.objects.all()
    for sub in subscriptions:
        sub.is_premium = False
        sub.started_at = None
        sub.expires_at = None
        sub.auto_renew = False
        sub.payment_method = ""
        sub.save()

    # Сбрасываем profile_settings
    from users.models import ProfileSettings

    profiles = ProfileSettings.objects.all()
    profiles.update(is_premium=False)

    print(f"✅ Сброшено {subscriptions.count()} подписок и {profiles.count()} профилей")


if __name__ == "__main__":
    reset_all_premium()
