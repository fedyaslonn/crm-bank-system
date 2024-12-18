from django.db import models
from django.contrib.auth import get_user_model
from customers.models import ClientCard
from users.models import UserClientCard

# Create your models here.

User = get_user_model()

class SalaryDepositManager(models.Manager):
    def create(self, user, card, amount):
        salary_deposit = self.model(
            user=user,
            card=card,
            amount=amount
        )

        salary_deposit.save(using=self._db)
        return salary_deposit


class SalaryDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_deposits')
    card = models.ForeignKey(UserClientCard, on_delete=models.CASCADE, related_name='salary_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма пополнения")
    deposited_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата пополнения")

    objects = SalaryDepositManager()

    class Meta:
        verbose_name = "Пополнение зарплаты"
        verbose_name_plural = "Пополнения зарплаты"
        ordering = ["-deposited_at"]
        db_table = "SalaryDeposit"
