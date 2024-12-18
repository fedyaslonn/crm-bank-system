from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django.db import models

from django.forms import ValidationError
from keyring.backends.libsecret import available

from users.models import CustomUser

from customers.models import ClientCard

# Create your models here.
User = get_user_model()


class Trades(models.Model):
    CHOICES = [
        ('CTU', 'Crypto_to_USD'),
        ('UTC', 'USD_to_Crypto')
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('FROZEN', 'Frozen'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    status = models.CharField(
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Статус трейда"
    )

    card = models.ForeignKey(ClientCard, verbose_name="Карта для списания", related_name='trades', on_delete=models.CASCADE, null=True)
    trades_type = models.CharField(choices=CHOICES, default='CTU', null=False, blank=False, verbose_name="Вид трейда")
    author = models.ForeignKey(User, related_name='trades_initiator', on_delete=models.CASCADE, verbose_name="Автор трейда")
    other_user = models.ForeignKey(CustomUser, related_name='other_user', on_delete=models.CASCADE, verbose_name="Пользователь, принимающий трейд", null=True, blank=True)

    amount_from = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=8,
        verbose_name="Количество валюты"
    )

    currency_from = models.CharField(
        default='USD',
        max_length=10,
        verbose_name="Валюта, которую предлагают"
    )

    amount_to = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=8,
        verbose_name="Количество валюты к обмену"
    )

    currency_to = models.CharField(
        default='USD',
        max_length=10,
        verbose_name="Валюта, которую хотят получить"
    )


    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания трейда")

    class Meta:
        verbose_name = "Трейд"
        verbose_name_plural = "Трейды"
        ordering = ["-created_at"]
        db_table = "Trades"

    def clean(self):
        if self.trades_type == 'UTC' and self.currency_from != 'USD':
            raise ValidationError("Для трейда USD в Крипто валюта 'Предлагаемая' должна быть USD.")
        if self.trades_type == 'CTU' and self.currency_to != 'USD':
            raise ValidationError("Для трейда Крипто в USD валюта 'Требуемая' должна быть USD.")
        if self.currency_from == self.currency_to:
            raise ValidationError("Валюты 'предлагаемая' и 'требуемая' не могут совпадать.")

        super().clean()

