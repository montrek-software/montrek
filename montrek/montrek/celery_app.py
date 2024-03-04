import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "montrek.settings")
app = Celery(
    "montrek",
)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_always_eager = settings.CELERY_TASK_ALWAYS_EAGER
app.autodiscover_tasks()
