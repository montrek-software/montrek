from typing import Any

from django.contrib.auth import get_user_model
from mailing.managers.mailing_manager import MailingManager
from tasks.montrek_task import MontrekTask

from api_upload.managers.api_upload_manager import ApiUploadManager


class ApiUploadTask(MontrekTask):
    api_upload_manager_class: type[ApiUploadManager]

    def __init__(self):
        task_name = f"{self.api_upload_manager_class.__module__}.{self.api_upload_manager_class.__name__}_process_file_task"
        super().__init__(task_name)

    def run(
        self,
        *args,
        session_data: dict[str, Any],
        **kwargs,
    ):
        self.session_data = session_data
        self.api_upload_manager = self.api_upload_manager_class(
            session_data=self.session_data
        )
        self._upload_and_process()
        self._send_mail()

    def _upload_and_process(self):
        self.upload_result = self.api_upload_manager.upload_and_process()

    def _send_mail(self):
        message = "<br>".join(
            [message.message for message in self.api_upload_manager.messages]
        )
        url = self.api_upload_manager.get_url()
        message += f"<br><br> <i>API: <a href='{url}'>{url}</a></i>"
        user = get_user_model().objects.get(pk=self.session_data["user_id"])
        if self.upload_result:
            subject = "API Upload successful"
        else:
            subject = "API Upload failed"
        MailingManager(session_data=self.session_data).send_montrek_mail(
            user.email, subject, message
        )
