import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver
from pymongo import MongoClient
from django.db.models.signals import post_save

from .models import Trades

import logging

logger = logging.getLogger(__name__)

MONGO_DATABASE_NAME = 'Notifications'
mongo_url = "mongodb+srv://wisp47344:Agcacjqf5144@cluster0.8093p.mongodb.net/"


client = MongoClient(mongo_url)
db = client[MONGO_DATABASE_NAME]
collection = db["Notification"]

@receiver(post_save, sender=Trades)
def trade_create_notification(sender, instance, created, **kwargs):
    if created:
        subject = "Успешное создание трейда"
        message = f"Ваш трейд {instance.id} был успешно создан. \n" \
                f"Сумма {instance.amount_from} - Валюта {instance.currency_from}"
        recipient_list = [instance.author.email]

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )

        except Exception as e:
            logger.info("Ошибка при создании уведомления")

        notification = {
            "user_id": instance.author.id,
            "title": "Успешное создание трейда",
            "content": message,
            "trade_id": instance.id,
            "created_at": datetime.datetime.utcnow()
        }

        try:
            result = collection.insert_one(notification)
        except Exception as e:
            logger.info("Ошибка при записи уведомления о трейде в MongoDB")