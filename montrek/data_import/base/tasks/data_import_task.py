from typing import Any
import re

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

    def __init__(
        self,
    ):
        manager_class = self.manager_class
        task_name = (
            f"{manager_class.__module__}.{manager_class.__name__}_process_file_task"
        )
        super().__init__(task_name, self.queue)



    def run(self, session_data: dict[str, Any], import_data: ImportDataType = {} ) -> str:
        self.session_data = session_data
        self.manager = self.manager_class(session_data)
        self.manager.process_import_data(import_data)
        self.send_mail()
        return self.get_message()

    def send_mail(self):
        user = get_user_model().objects.get(pk=self.session_data["user_id"])
        registry_entry = self.manager.get_registry()
        subject_name = self.get_subject_name()
        if registry_entry.import_status == "processed":
            if not self.manager.send_mail():
                return
            subject = f"{subject_name} successful"
        else:
            subject = f"ERROR: {subject_name} unsuccessful"
        message = self.get_message()
        MailingManager(session_data=self.session_data).send_montrek_mail(
            user.email, subject, message
        )

    def get_message(self) -> str:
        return self.manager.get_message()

    def get_subject_name(self) -> str:
        return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", self.__class__.__name__)
