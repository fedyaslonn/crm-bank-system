import datetime
import string
import random

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dulwich.porcelain import status

from .dto import UserDTO, RequestDTO
from .tasks import send_registration_notification


# Create your models here.

class CustomUserManager(BaseUserManager):
    def get_user_by_id(self, user_id):
        return self.model.objects.get(id=user_id)

    def create_user(self, user_dto: UserDTO):
        if not user_dto.email:
            raise ValueError("Поле email должно быть определено")

        existing_admins = self.get_all_admins().exists()

        if user_dto.role == 'AD' and not existing_admins:
            user = self.create_superuser(
                username=user_dto.username,
                email=user_dto.email,
                password=user_dto.password,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
                role=user_dto.role,
                profile_photo=user_dto.profile_photo
            )
            user.set_password(user_dto.password)
            user.save(using=self._db)
            return user

        user = self.model(
            username=user_dto.username,
            email=self.normalize_email(user_dto.email),
            first_name=user_dto.first_name,
            last_name=user_dto.last_name,
            role='US',
            profile_photo=user_dto.profile_photo
        )

        user.set_password(user_dto.password)
        user.save(using=self._db)

        if user_dto.role != 'US':
            request_dto = RequestDTO(
                user=user.id,
                requested_role=user_dto.role,
                status='Pending',
                submitted_at=timezone.now()
            )
            RegistrationRequest.objects.create_request(request_dto)

        return user

    def create_superuser(self, username, email, password, first_name='', last_name='', profile_photo=None, **extra_fields):
        user_dto = UserDTO(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='AD',
            profile_photo=profile_photo or ''
        )
        user = self.model(username=user_dto.username,
                          email=user_dto.email,
                          first_name=user_dto.first_name,
                          last_name=user_dto.last_name,
                          role=user_dto.role,
                          profile_photo=user_dto.profile_photo)

        user.set_password(user_dto.password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def get_roles(self):
        return CustomUser.USER_ROLES

    def get_all_admins(self):
        return self.filter(is_superuser=True)

    def get_all_users(self):
        return self.all()

class CustomUser(AbstractBaseUser):
    USER_ROLES = [
        ("AD", "admin"),
        ("US", "user"),
    ]
    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    role = models.CharField(max_length=2, choices=USER_ROLES, help_text="Роль пользователя", blank=False, null=False)
    profile_photo = models.URLField(help_text="Фото профиля", blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Зарплата пользователя")
    trades_count = models.IntegerField(default=0, verbose_name="Количество совершенных трейдов")
    has_used_promo = models.BooleanField(default=False, verbose_name="Использовал ли пользователь чужой промокод")
    has_permanent_discount = models.BooleanField(
        default=False,
        verbose_name="Пользователь получил постоянную скидку на комиссию"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Модель пользователя"
        indexes = [
            models.Index(fields=["username", "first_name", "last_name"])
        ]
        db_table = 'Users'

    @staticmethod
    def generate_random_string(length=8):
        characters = string.ascii_letters
        random_string = ''.join(random.choice(characters) for _ in range(length))
        random_string = ''.join(random.choice([c.upper(), c.lower()]) for c in random_string)
        return random_string

    def __str__(self):
        return f"{self.username}"

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser or self.is_staff


class RegistrationRequestManager(models.Manager):
    def create_request(self, request_dto: RequestDTO):
        user = CustomUser.objects.get_user_by_id(request_dto.user)
        request = self.model(
            user=user,
            requested_role=request_dto.requested_role,
            status=request_dto.status,
            submitted_at=request_dto.submitted_at
        )

        request.save(using=self._db)
        return request

    def approve(self, request_id):
        request = get_object_or_404(self.model, id=request_id)
        request.status = 'Approved'
        request.user.role = request.requested_role
        request.user.save(using=self._db)
        request.save(using=self._db)
        send_registration_notification(request.user.email)
        request.delete()

    def reject(self, request_id):
        request = get_object_or_404(self.model, id=request_id)
        request.status = 'Rejected'
        request.save(using=self._db)
        request.delete()

    def get_all_pending(self):
        return self.filter(status="Pending")

    def get_by_id(self, request_id):
        return self.get(id=request_id)

class RegistrationRequest(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    requested_role = models.CharField(max_length=2, choices=CustomUser.USER_ROLES, help_text="Запрашиваемая роль")
    status = models.CharField(
        max_length=10,
        choices=[("Pending", "В ожидании"), ("Approved", "Одобрено"), ("Rejected", "Отклонено")],
        default="Pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    objects = RegistrationRequestManager()

    def __str__(self):
        return f"Запрос на регистрацию от пользователя {self.user.username} для роли {self.get_requested_role_display()}"


class UserClientCard(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=16, decimal_places=2, default=0, verbose_name="Баланс на карте в USD")
    card_number = models.CharField(max_length=16, unique=True, verbose_name="Номер карты",
                                   validators=[MinLengthValidator(16, message="Номер карты должен быть минимум 16 символов"),
                                                MaxLengthValidator(16, message="Номер карты должен быть максимум 16 символов")])
    expiration_date = models.DateTimeField(verbose_name="Срок действия")
    is_active = models.BooleanField(default=True, verbose_name="Активна", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления", blank=True, null=True)

    class Meta:
        verbose_name = "Карта клиента"
        verbose_name_plural = "Криптовалютные карты клиентов"
        ordering = ["-created_at"]
        db_table = "Client_Cards"

    def __str__(self):
        return f"Карта {self.card_number} клиента {self.user.username}"

    def get_masked_card_number(self):
        return f"{self.card_number[:4]} **** **** {self.card_number[-4:]}"

    @classmethod
    def earliest(cls, user):
        return cls.objects.filter(user=user).order_by('created_at').first()

class Promos(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='promo')
    promo_code = models.CharField(max_length=8, verbose_name="Промокод")
    promo_usage = models.IntegerField(default=0, verbose_name="Количество пользователей, которые ввели промокод")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата использования")


    class Meta:
        verbose_name = "Использование промокода"
        verbose_name_plural = "Использования промокодов"
        unique_together = ('user', 'promo_code')
        db_table = "Promos"

    def __str__(self):
        return f"{self.promo_code}"
