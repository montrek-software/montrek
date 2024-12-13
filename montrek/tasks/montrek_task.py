from celery import Task
from montrek.celery_app import app as celery_app
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)


class MontrekTask(Task):
    queue = PARALLEL_QUEUE_NAME
    is_register_on_subclass_init = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name") or not cls.name:
            cls.name = f"{cls.__module__}.{cls.__name__}"  # Set a default task name
        if cls.is_register_on_subclass_init:
            cls.register_task()

    @classmethod
    def register_task(cls, **kwargs):
        celery_app.register_task(cls, **kwargs)
