from montrek.celery_app import app as celery_app
from celery import Task


class DownloadTableTask(Task):
    name = "reporting.tasks.download_table_tasks.DownloadTableTask"

    def __init__(self, *args, manager, filetype: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.filetype = filetype

        celery_app.register_task(self)

    def run(self, *args, **kwargs) -> str:
        self.manager.send_table_by_mail(self.filetype)
        return "Table sent by mail."


@celery_app.task
def download_table_task(manager, filetype) -> str:
    manager.send_table_by_mail(filetype)
    return "Table sent by mail."
