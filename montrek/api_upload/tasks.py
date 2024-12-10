from typing import Any

from celery import Task
from django.contrib.auth import get_user_model
from mailing.managers.mailing_manager import MailingManager
from montrek.celery_app import app as celery_app

from api_upload.managers.api_upload_manager import ApiUploadManager


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
        self._run(api_upload_manager)
        self._send_mail(api_upload_manager)

    def _run(self, api_upload_manager: ApiUploadManager):
        self.upload_result = api_upload_manager.upload_and_process()

    def _send_mail(self, api_upload_manager: ApiUploadManager):
        message = "<br>".join(
            [message.message for message in api_upload_manager.messages]
        )
        user = get_user_model().objects.get(pk=self.session_data["user_id"])
        if self.upload_result:
            subject = "API Upload successful"
        else:
            subject = "API Upload failed"
        MailingManager(session_data=self.session_data).send_montrek_mail(
            user.email, subject, message
        )
