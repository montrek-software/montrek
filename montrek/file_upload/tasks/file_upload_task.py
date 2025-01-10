from typing import Any, Dict
from django.contrib.auth import get_user_model
from baseclasses.managers.montrek_manager import MontrekManager
from tasks.montrek_task import MontrekTask
from mailing.managers.mailing_manager import MailingManager


class FileUploadTask(MontrekTask):
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

    def run(self, session_data: Dict[str, Any]):
        manager = self.manager_class(session_data)
        result = manager.process()
        message = manager.processor.message
        user = get_user_model().objects.get(pk=session_data["user_id"])
        if result:
            subject = "Background file processing finished successfully."
        else:
            subject = "ERROR: Background file processing did not finish successfully!"
        MailingManager(session_data=session_data).send_montrek_mail(
            user.email, subject, message
        )
        return message
