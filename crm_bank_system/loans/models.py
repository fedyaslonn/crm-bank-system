from django.db import models
from django.contrib.auth import get_user_model

from users.models import CustomUser

# Create your models here.


User = get_user_model()

class LoanManager(models.Manager):
    def create_loan(self, loan_dto):
        loan = self.model(
            amount=loan_dto.amount,
            interest_rate=loan_dto.interest_rate,
            term=loan_dto.term,
        )

        loan.save(using=self._db)
        return loan

    def get_loans(self):
        return self.all()

class Loan(models.Model):
    status_choices = [
        ('NOT_SELECTED', 'Not_selected'),
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid')
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма кредита")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Процентная ставка")
    term = models.PositiveIntegerField(verbose_name="Сумма кредита")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления", blank=True, null=True)
    status = models.CharField(max_length=20, choices=status_choices, default='NOT_SELECTED', verbose_name='Статус кредита')
    user = models.ForeignKey(CustomUser, default=1, null=True, blank=True, on_delete=models.CASCADE, related_name="loans", verbose_name="Пользователь")

    objects = LoanManager()

    class Meta:
        verbose_name = "Кредит"
        verbose_name_plural = "Кредиты"
        ordering = ["-created_at"]
        db_table = "Loans"

class LoanRequestManager(models.Manager):
    def verify_if_request_unique(self, user):
        if self.filter(user=user, status='PENDING').exists():
            raise ValueError("У вас уже есть заявка на рассмотрении")

        return True

    def get_loans(self):
        return self.select_related('user', 'loan').filter(status='PENDING')

class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(CustomUser, null=True, blank=True, on_delete=models.CASCADE, related_name="loan_requests", verbose_name="Пользователь")
    loan = models.OneToOneField(Loan, null=True, blank=True, on_delete=models.CASCADE, related_name="loan_request", verbose_name="Пользователь")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING", verbose_name="Статус заявки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    comments = models.TextField(blank=True, null=True, verbose_name="Комментарии специалиста")

    objects = LoanRequestManager()

    class Meta:
        verbose_name = "Заявка на кредит"
        verbose_name_plural = "Заявки на кредит"
        ordering = ["-created_at"]
        db_table = "LoanRequests"