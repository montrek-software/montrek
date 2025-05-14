from django.contrib import messages
from django.http import HttpResponseRedirect
import os

from celery import Celery
from kombu import Queue

SEQUENTIAL_QUEUE_NAME = "sequential_queue"
PARALLEL_QUEUE_NAME = "parallel_queue"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "montrek.settings")
app = Celery(
    "montrek",
)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_queues = (
    Queue(SEQUENTIAL_QUEUE_NAME, routing_key=f"{SEQUENTIAL_QUEUE_NAME}.#"),
    Queue(PARALLEL_QUEUE_NAME, routing_key=f"{PARALLEL_QUEUE_NAME}.#"),
)

app.conf.task_default_queue = SEQUENTIAL_QUEUE_NAME

app.autodiscover_tasks()


def revoke_task(request, task_id):
    previous_url = request.META.get("HTTP_REFERER")
    try:
        app.control.revoke(task_id, terminate=True)
        messages.info(
            request,
            f"Task {task_id} has been revoked.",
        )
    except Exception as e:
        messages.error(
            str(e),
        )
    return HttpResponseRedirect(previous_url)
