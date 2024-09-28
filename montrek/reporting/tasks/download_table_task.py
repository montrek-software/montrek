from montrek.celery_app import app as celery_app
from celery import Task


class DownloadTableTask(Task):
    def __init__(self, *args, manager_class, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager_class = manager_class

        celery_app.register_task(self)

    def run(self, *args, filetype, session_data: dict, **kwargs) -> str:
        self.manager_class(session_data).send_table_by_mail(filetype)
        return "Table sent by mail."


@celery_app.task
def download_table_task(manager, filetype) -> str:
    manager.send_table_by_mail(filetype)
    return "Table sent by mail."
