import os
import sys
from celery import Celery

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info(f"Путь: {sys.path}")
logger.debug(f"DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE')}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_bank_system.settings')

app = Celery('crm_bank_system')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')