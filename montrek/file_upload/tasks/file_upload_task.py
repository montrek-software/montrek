import logging

from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.typing import SessionDataType
from django.contrib.auth import get_user_model
from mailing.managers.mailing_manager import MailingManager
from tasks.montrek_task import MontrekTask

logger = logging.getLogger(__name__)


class FileUploadTask(MontrekTask):
    success_message = "Background file processing finished successfully."
    failure_message = "ERROR: Background file processing did not finish successfully!"
    mailing_manager_class: type[MailingManager] = MailingManager

    def __init__(
        self,
        manager_class: type[MontrekManager],
        queue: str,
    ):
        self.manager_class = manager_class
        task_name = (
            f"{manager_class.__module__}.{manager_class.__name__}_process_file_task"
        )
        super().__init__(task_name, queue)

    def run(self, session_data: SessionDataType):
        logger.debug("Start task run")
        manager = self.manager_class(session_data)
        logger.debug("%s: manager: %s", self.__class__.__name__, manager)
        result = manager.process()
        message = self.send_result_mail(manager, session_data, result)
        logger.debug("End task run")
        return message

    def send_result_mail(
        self, manager: MontrekManager, session_data: SessionDataType, result: bool
    ) -> str:
        message = manager.processor.message
        user = get_user_model().objects.get(pk=session_data["user_id"])
        if result:
            subject = self.success_message
        else:
            subject = self.failure_message
        self.mailing_manager_class(session_data=session_data).send_montrek_mail(
            user.email, subject, message
        )
        return message
