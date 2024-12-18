from datetime import datetime
from pyexpat.errors import messages

from celery import shared_task
from celery.worker.consumer.mingle import exception
from django.core.mail import send_mail
from django.conf import settings

from django.db import transaction

from .dto import UserDTO

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@shared_task(queue='registration_notification')
def send_registration_notification(user_email):
    send_mail(
        'Регистрация подтверждена',
        'Ваша регистрация была подтверждена администратором',
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )

@shared_task(queue='admin_registration_notification')
def send_admin_notification(user_dto):
    required_keys = ['username', 'role']
    for key in required_keys:
        if key not in user_dto:
            raise ValueError(f"Отсутствует ключ '{key}' в user_dto")

    admin_email = settings.DEFAULT_FROM_EMAIL
    subject = 'Новый запрос на регистрацию'
    message = f"Пользователь {user_dto['username']} запросил роль {user_dto['role']}."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email],
        fail_silently=False,
    )

@shared_task(queue='salary')
def add_salary_to_card():
    logger.info("Начало выполнения задачи")
    from .models import CustomUser
    from users.models import UserClientCard
    from payments.models import SalaryDeposit
    try:
        users = CustomUser.objects.filter(is_active=True)
        for user in users:
            logger.info(f"Обработка пользователя: {user.id}")
            with transaction.atomic():
                cards = UserClientCard.objects.filter(user=user).order_by('created_at')
                if cards.exists():
                    card = cards.first()
                    logger.info(f"Карта найдена: {card.id}, баланс: {card.balance}")
                    deposit = SalaryDeposit.objects.create(
                        user=user,
                        card=card,
                        amount=user.salary
                    )
                    logger.info(f"Депозит создан: {deposit.id}, сумма: {deposit.amount}")
                    card.balance += deposit.amount
                    card.save()
                    logger.info(f"Баланс обновлен: {card.balance}")
    except Exception as e:
        logger.error(f"Ошибка в задаче: {str(e)}")
        raise e

@shared_task(queue='pass_recovery')
def send_verification_code(user_email, code):
    send_mail(
    "Код подтверждения для восстановления пароля",
    f"Ваш код подтверждения {code}",
    settings.DEFAULT_FROM_EMAIL,
    [user_email],
    fail_silently=False
    )

@shared_task(queue='login_pass')
def send_login_pass(user_email):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_mail(
        f"Вход в аккаунт"
        f"На ваш аккаунт был выполнен вход {current_time}. Если это были не вы, пожалуйста свяжитесь с поддержкой.",
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False
    )