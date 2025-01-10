from celery import Task
from montrek.celery_app import app as celery_app
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)


class MontrekTask(Task):
    def __init__(self, task_name: str = "", queue: str = PARALLEL_QUEUE_NAME):
        task_name = (
            task_name or f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.raise_for_conflicting_task_name(task_name)
        self.name = task_name
        self.queue = queue
        celery_app.register_task(self)

    def raise_for_conflicting_task_name(self, task_name: str):
        registered_tasks = celery_app.tasks.keys()
        if task_name in registered_tasks:
            raise ValueError(
                f"Task with name {task_name} already registered. Please choose a different name."
            )
