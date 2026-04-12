"""
Миграция для создания моделей подписки
"""
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
from datetime import timedelta


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_cover_image'),
    ]

    operations = [
        # Модель подписки
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='users.user')),
                ('is_active', models.BooleanField(default=False, verbose_name='Подписка активна')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата начала')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата окончания')),
                ('auto_renew', models.BooleanField(default=True, verbose_name='Автопродление')),
                ('payment_method', models.CharField(blank=True, max_length=50, verbose_name='Способ оплаты')),
                ('transaction_id', models.CharField(blank=True, max_length=100, verbose_name='ID транзакции')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Подписка',
                'verbose_name_plural': 'Подписки',
            },
        ),
        
        # Модель промокода
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Код')),
                ('discount_percent', models.PositiveIntegerField(default=0, verbose_name='Скидка %')),
                ('discount_amount', models.PositiveIntegerField(default=0, verbose_name='Скидка в рублях')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('max_uses', models.PositiveIntegerField(default=1, verbose_name='Максимум использований')),
                ('used_count', models.PositiveIntegerField(default=0, verbose_name='Использовано')),
                ('valid_until', models.DateTimeField(blank=True, null=True, verbose_name='Действителен до')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Промокод',
                'verbose_name_plural': 'Промокоды',
            },
        ),
        
        # Модель использования промокода
        migrations.CreateModel(
            name='PromoCodeUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('promo_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='users.promocode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promo_usages', to='users.user')),
                ('used_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Использование промокода',
                'verbose_name_plural': 'Использования промокодов',
            },
        ),
    ]
