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

# Only take the task off the queue after it has been acknowledged (executed) by
# the worker. This is to prevent the task from being lost if the worker dies
# before the task is executed.
app.conf.task_acks_late = True
# If the worker dies before the task is executed, reject the task so that it can
# be re-queued.
app.conf.task_reject_on_worker_lost = True
# number of messages the worker can prefetch from the queue
app.conf.prefetch_multiplier = 1
# time to wait for the worker to acknowledge the task before the message is re-queued
# app.conf.broker_transport_options = {"visibility_timeout": 3600}

app.autodiscover_tasks()
