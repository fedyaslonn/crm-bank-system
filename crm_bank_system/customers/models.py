from decimal import Decimal
from locale import currency

from django.core.exceptions import ValidationError

from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from users.models import CustomUser


# Create your models here.


def set_default_currencies_list():
    return ['BTC', 'ETH', 'USDT', 'SOL', 'XPR']

def set_default_balance():
    return {'BTC': 0, 'ETH': 0, 'USDT': 0, 'SOL': 0, 'XPR': 0}

class ClientCardManger(models.Manager):
    def create_card(self, card_dto):
        card = self.model(
            user=card_dto.user,
            card_number=card_dto.card_number,
            expiration_date=card_dto.expiration_date,
            balance=card_dto.balance,
            wallet_address=card_dto.wallet_address
        )

        card.save(using=self._db)
        return card

    def deposit(self, card, amount):
        if amount > 0:
            card.balance += amount
            card.save(using=self._db)

        else:
            raise ValueError("Сумма пополнения должна быть положительной")

    def withdraw(self, card, amount):
        if amount > 0 and amount <= card.balance:
            card.balance -= amount
            card.save(using=self._db)
        else:
            raise ValueError("Недостаточно средств на карте")

    def get_cards_by_user(self, user_id, search_query=''):
        cards = self.filter(user_id=user_id, is_active=True)
        if search_query:
            cards = cards.filter(
                Q(card_type__icontains=search_query)
            )
        return cards

    def get_card_by_card_number(self, card_num):
        return self.get(card_number=card_num)

    def get_first_created_card(self, user):
        return self.filter(user=user).order_by('created_at').first()

class ClientCard(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16, unique=True, verbose_name="Номер криптовалютной карты",
                                   validators=[MinLengthValidator(16, message="Номер карты должен быть минимум 16 символов"),
                                                MaxLengthValidator(16, message="Номер карты должен быть максимум 16 символов")])
    expiration_date = models.DateField(verbose_name="Срок действия")
    wallet_address = models.CharField(
        max_length=42,
        unique=True,
        verbose_name="Адрес криптокошелька",
        blank=True,
        null=True
    )
    supported_currencies = models.JSONField(
        default=set_default_currencies_list,
        verbose_name="Поддерживаемые криптовалюты",
        help_text="Список криптовалют (например: ['BTC', 'ETH', 'USDT'])."
    )

    balance = models.JSONField(
        default=set_default_balance,
        verbose_name="Баланс",
        help_text="Баланс по каждой криптовалюте (например: {'BTC': 0.5, 'ETH': 2})."
    )

    balance_in_usd = models.DecimalField(max_digits=16, decimal_places=2, default=0, verbose_name="Баланс на карте в USD", validators=[MinValueValidator(0)])

    transaction_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.01,
        validators=[MinValueValidator(Decimal('0.0'))],
        verbose_name="Комиссия за транзакции (%)"
    )

    is_active = models.BooleanField(default=True, verbose_name="Активна", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления", blank=True, null=True)

    objects = ClientCardManger()

    class Meta:
        verbose_name = "Криптовалютная карта клиента"
        verbose_name_plural = "Криптовалютные карты клиентов"
        ordering = ["-created_at"]
        db_table = "Crypto_client_Cards"

    def __str__(self):
        return f"Крипто-карта {self.card_number} клиента {self.user.username}"

    def get_masked_card_number(self):
        return f"{self.card_number[:4]} **** **** {self.card_number[-4:]}"

    def get_balance_in_usd(self, user, card_id):
        try:
            card = self.get(id=card_id)
        except self.model.DoesNotExist:
            raise ValidationError(f"Карта с поддерживаемой валютой {currency} не найдена.")

        balance = Decimal(card.balance_in_usd)
        return balance

    def get_total_balance_in_crypto(self, user, currency):
        currency = currency.upper()
        card = self.filter(user=user, supported_currencies__contains=[currency])
        balance_in_currency = Decimal(card.balance.get(currency, '0'))

        return balance_in_currency


    def update_balance(self, currency, amount):
        currency = currency.upper()
        self.balance = self.balance or {}
        current_balance = Decimal(self.balance.get(currency, '0'))
        amount = Decimal(amount)
        self.balance[currency] = str(current_balance + amount)
        self.save()


    def calculate_transaction_fee(self, amount):
        return (amount * self.transaction_fee_percentage) / 100

    def deduct_balance(self, currency, amount):
        amount = Decimal(amount)
        if currency == 'USD':
            if self.balance_in_usd < amount:
                raise ValidationError(f"Недостаточно {currency} на карте.")
            self.balance_in_usd -= amount
        else:
            current_balance = Decimal(self.balance.get(currency, '0'))
            if current_balance < amount:
                raise ValidationError(f"Недостаточно {currency} на карте.")
            self.balance[currency] = str(current_balance - amount)
        self.save()

    def add_balance(self, currency, amount):
        amount = Decimal(amount)
        if currency == 'USD':
            self.balance_in_usd += amount
        else:
            current_balance = Decimal(self.balance.get(currency, '0'))
            self.balance[currency] = str(current_balance + amount)
        self.save()

    def save(self, *args, **kwargs):
        if not isinstance(self.balance, dict):
            self.balance = set_default_balance()
        super().save(*args, **kwargs)
