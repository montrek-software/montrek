from typing import Any
from celery import Task
from api_upload.managers.api_upload_manager import ApiUploadManager
from montrek.celery_app import app as celery_app


class ApiUploadTask(Task):
    api_upload_manager_class: type[ApiUploadManager]

    def __init__(self, *args, session_data: dict[str, Any], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.upload_result: bool = False
        self.session_data = session_data
        celery_app.register_task(self)

    def run(self, *args, **kwargs):
        api_upload_manager = self.api_upload_manager_class(
            session_data=self.session_data
        )
        self.upload_result = api_upload_manager.upload_and_process()
