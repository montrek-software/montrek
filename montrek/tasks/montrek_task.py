from celery import Task
from montrek.celery_app import app as celery_app
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)


class MontrekTask(Task):
    queue = PARALLEL_QUEUE_NAME

    def __init__(self, task_name: str):
        self.name = task_name
        celery_app.register_task(self)
