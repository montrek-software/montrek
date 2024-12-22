from celery import Task
from montrek.celery_app import app as celery_app
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)


class MontrekTask(Task):
    def __init__(self, task_name: str, queue: str = PARALLEL_QUEUE_NAME):
        self.name = task_name
        self.queue = queue
        celery_app.register_task(self)
