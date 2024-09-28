from montrek.celery_app import app as celery_app
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)
from celery import Task


class DownloadTableTask(Task):
    queue = PARALLEL_QUEUE_NAME

    def __init__(self, *args, manager_class, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager_class = manager_class
        self.name = f"reporting.tasks.{self.manager_class.__name__}_download_table"

        celery_app.register_task(self)

    def run(self, *args, filetype, session_data: dict, **kwargs) -> str:
        self.manager_class(session_data).send_table_by_mail(filetype)
        return "Table sent by mail."
