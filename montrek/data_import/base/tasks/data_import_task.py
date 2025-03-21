from typing import Any

from data_import.base.managers.data_import_managers import DataImportManagerABC
from data_import.types import ImportDataType
from django.contrib.auth import get_user_model
from mailing.managers.mailing_manager import MailingManager
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)
from tasks.montrek_task import MontrekTask


class DataImportTask(MontrekTask):
    manager_class: type[DataImportManagerABC]
    queue: str = PARALLEL_QUEUE_NAME
    success_subject: str | None = None

    def __init__(
        self,
        session_data: dict[str, Any],
    ):
        self.session_data = session_data
        manager_class = self.manager_class
        task_name = (
            f"{manager_class.__module__}.{manager_class.__name__}_process_file_task"
        )
        super().__init__(task_name, self.queue)
        self.manager = manager_class(session_data)

    def run(self, import_data: ImportDataType) -> str:
        self.manager.process_import_data(import_data)
        self.send_mail()
        return self.get_message()

    def send_mail(self):
        user = get_user_model().objects.get(pk=self.session_data["user_id"])
        subject = self.success_subject
        message = self.get_message()
        MailingManager(session_data=self.session_data).send_montrek_mail(
            user.email, subject, message
        )

    def get_message(self) -> str:
        return self.manager.get_message()

    # def run(self, session_data: Dict[str, Any]):
    #     manager = self.manager_class(session_data)
    #     result = manager.process()
    #     message = manager.processor.message
    #     user = get_user_model().objects.get(pk=session_data["user_id"])
    #     if result:
    #         subject = "Background file processing finished successfully."
    #     else:
    #         subject = "ERROR: Background file processing did not finish successfully!"
    #     MailingManager(session_data=session_data).send_montrek_mail(
    #         user.email, subject, message
    #     )
    #     return message
