from django.contrib import messages
from django.http import HttpResponseRedirect
import os

from celery import Celery
from django.urls import resolve
from urllib.parse import urlparse
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


def revoke_file_upload_task(request, task_id):
    previous_url = request.META.get("HTTP_REFERER")
    try:
        app.control.revoke(task_id, terminate=True)
        messages.info(request, f"Task {task_id} has been revoked.")
    except Exception as e:
        messages.error(request, str(e))
    if not previous_url:
        return HttpResponseRedirect("/")
    previous_match = resolve(urlparse(previous_url).path)
    view_class = previous_match.func.view_class
    repository_class = view_class.manager_class.repository_class
    session_data = previous_match.kwargs
    session_data["user_id"] = request.user.id
    registry_repository = repository_class(session_data)
    registry = registry_repository.receive().get(celery_task_id=task_id)
    redirect = HttpResponseRedirect(previous_url)
    if not registry:
        messages.error(request, f"Task {task_id} not found in registry.")
        return redirect
    registry_dict = registry_repository.object_to_dict(registry)
    registry_dict["upload_status"] = "revoked"
    registry_dict["upload_message"] = "Task has been revoked."
    registry_repository.create_by_dict(registry_dict)
    return redirect
