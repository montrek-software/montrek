from celery import Task
from montrek.celery_app import app as celery_app


class ApiUploadTask(Task):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        celery_app.register_task(self)

    def run(self, *args, **kwargs):
        # do something
        pass
