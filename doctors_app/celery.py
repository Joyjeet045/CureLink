import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doctors_app.settings')

app = Celery('doctors_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() 