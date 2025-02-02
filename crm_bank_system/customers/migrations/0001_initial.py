# Generated by Django 5.1.3 on 2024-11-29 22:45

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_number', models.CharField(max_length=16, unique=True, validators=[django.core.validators.MinLengthValidator(16, message='Номер карты должен быть минимум 16 символов'), django.core.validators.MaxLengthValidator(16, message='Номер карты должен быть максимум 16 символов')], verbose_name='Номер криптовалютной карты')),
                ('expiration_date', models.DateField(verbose_name='Срок действия')),
                ('wallet_address', models.CharField(blank=True, max_length=42, null=True, unique=True, verbose_name='Адрес криптокошелька')),
                ('supported_currencies', models.JSONField(default=['BTC', 'ETH', 'USDT', 'SOL', 'XPR'], help_text="Список криптовалют (например: ['BTC', 'ETH', 'USDT']).", verbose_name='Поддерживаемые криптовалюты')),
                ('balance', models.JSONField(default=0, help_text="Баланс по каждой криптовалюте (например: {'BTC': 0.5, 'ETH': 2}).", verbose_name='Баланс')),
                ('transaction_fee_percentage', models.DecimalField(decimal_places=2, default=0.5, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.0'))], verbose_name='Комиссия за транзакции (%)')),
                ('is_active', models.BooleanField(blank=True, default=True, null=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Криптовалютная карта клиента',
                'verbose_name_plural': 'Криптовалютные карты клиентов',
                'db_table': 'Crypto_client_Cards',
                'ordering': ['-created_at'],
            },
        ),
    ]
