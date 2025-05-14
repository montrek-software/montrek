from django.http import JsonResponse
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


def kill_task(request, task_id):
    try:
        app.control.revoke(task_id, terminate=True)
        return JsonResponse(
            {"status": "success", "message": f"Task {task_id} has been revoked."}
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
