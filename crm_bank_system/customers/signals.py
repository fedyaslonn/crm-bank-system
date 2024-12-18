import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver
from pymongo import MongoClient
from django.db.models.signals import post_save

from .models import ClientCard

import logging

logger = logging.getLogger(__name__)

MONGO_DATABASE_NAME = 'Notifications'
mongo_url = "mongodb+srv://wisp47344:Agcacjqf5144@cluster0.8093p.mongodb.net/"


client = MongoClient(mongo_url)
db = client[MONGO_DATABASE_NAME]
collection = db["Notification"]


@receiver(post_save, sender=ClientCard)
def card_create_notification(sender, instance, created, **kwargs):
    if created:
        subject = "Успешное создание криптокарты!"
        message = (f"Уважаемый {instance.user.first_name} {instance.user.last_name}, карта с номером '{instance.card_number}' была успешно создана."
                   f"Дата окончания действия карты {instance.expiration_date}")
        recipient_list = [instance.user.email]

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )

        except Exception as e:
            logger.info(f"Ошибка при создании уведомления {str(e)}")

        notification = {
            "user_id": instance.user.id,
            "title": "Успешное создание криптокарты",
            "content": message,
            "card_id": instance.id,
            "created_at": datetime.datetime.utcnow()
        }

        try:
            result = collection.insert_one(notification)
        except Exception as e:
            logger.info("Ошибка при записи уведомления о карте в MongoDB")