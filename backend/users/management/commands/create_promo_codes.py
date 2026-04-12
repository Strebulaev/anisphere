"""
Management command to create default promo codes
"""
from django.core.management.base import BaseCommand
from users.models import PromoCode


class Command(BaseCommand):
    help = 'Creates default promo codes for subscription discounts'

    def handle(self, *args, **options):
        # Создаем промокод Ani10 - 10% скидка
        promo, created = PromoCode.objects.get_or_create(
            code='ANI10',
            defaults={
                'discount_percent': 10,
                'discount_amount': 0,
                'is_active': True,
                'max_uses': 1000,
                'used_count': 0,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Промокод ANI10 создан (10% скидка, {promo.max_uses} использований)'))
        else:
            promo.discount_percent = 10
            promo.max_uses = 1000
            promo.is_active = True
            promo.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Промокод ANI10 обновлен'))
        
        # Также создаем тестовый промокод для полной активации
        promo_test, created_test = PromoCode.objects.get_or_create(
            code='FREE',
            defaults={
                'discount_percent': 0,
                'discount_amount': 399,  # Полная стоимость
                'is_active': True,
                'max_uses': 100,
                'used_count': 0,
            }
        )
        
        if created_test:
            self.stdout.write(self.style.SUCCESS(f'✓ Промокод FREE создан (бесплатная подписка, {promo_test.max_uses} использований)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Промокод FREE уже существует'))
        
        self.stdout.write(self.style.SUCCESS('\nГотово! Промокоды созданы.'))
