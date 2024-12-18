from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()

class TransactionManager(models.Manager):
    def create_transaction(self, transaction_dto):
        transaction = self.model(
            sender = transaction_dto.sender,
            recipient = transaction_dto.recipient,
            amount = transaction_dto.amount,
            currency_from = transaction_dto.currency_from,
            currency_to = transaction_dto.currency_to,
            type=transaction_dto.type,
            status='COMPLETED'
        )

        transaction.save(using=self._db)
        return transaction

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    TYPE_CHOICES = [
        ("REPLENISHMENT", "Replenishment"),
        ("TRADE", "Trade")
    ]

    status = models.CharField(choices=STATUS_CHOICES, default="Pending", verbose_name="Статус транзакции")
    type = models.CharField(choices=TYPE_CHOICES, default="REPLENISHMENT", verbose_name="Вид транзакции")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Отправитель', related_name="sent_transactions")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Получатель", related_name="received_transactions", blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    currency_from = models.CharField(
        default='USD',
        max_length=10,
        verbose_name="Валюта 1"
    )
    currency_to = models.CharField(
        default='USD',
        max_length=10,
        verbose_name="Валюта 2"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = TransactionManager()

    class Meta:
        verbose_name = "Транзакция"
        db_table = "Transactions"
        verbose_name_plural = "Транзакции"
        ordering = ["-created_at"]