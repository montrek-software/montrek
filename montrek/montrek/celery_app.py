import os

from celery import Celery
from django.conf import settings
from kombu import Queue

SEQUENTIAL_QUEUE_NAME = "sequential_queue"
PARALLEL_QUEUE_NAME = "parallel_queue"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "montrek.settings")
app = Celery(
    "montrek",
)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_always_eager = settings.CELERY_TASK_ALWAYS_EAGER
app.conf.task_queues = (
    Queue(SEQUENTIAL_QUEUE_NAME, routing_key=f"{SEQUENTIAL_QUEUE_NAME}.#"),
    Queue(PARALLEL_QUEUE_NAME, routing_key=f"{PARALLEL_QUEUE_NAME}.#"),
)
app.conf.task_default_queue = SEQUENTIAL_QUEUE_NAME

app.autodiscover_tasks()
