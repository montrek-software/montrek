import logging
from urllib.parse import urlparse

from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.typing import SessionDataType
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import resolve
from mailing.managers.mailing_manager import MailingManager
from tasks.montrek_task import MontrekTask

from montrek.celery_app import app as celery_app

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


def revoke_file_upload_task(request, task_id: str):
    """
    Kill a running celery file upload task and update the corresponding
    registry entry.
    """
    previous_url = request.META.get("HTTP_REFERER")
    try:
        celery_app.control.revoke(task_id, terminate=True)
        messages.info(request, f"Task {task_id} has been revoked.")
    except Exception as e:
        messages.error(request, str(e))
    if not previous_url:
        return HttpResponseRedirect("/")
    previous_match = resolve(urlparse(previous_url).path)
    view_class = previous_match.func.view_class
    repository_class = view_class.manager_class.repository_class
    session_data = previous_match.kwargs
    session_data["user_id"] = request.user.id
    registry_repository = repository_class(session_data)
    registry = registry_repository.receive().get(celery_task_id=task_id)
    redirect = HttpResponseRedirect(previous_url)
    if not registry:
        messages.error(request, f"Task {task_id} not found in registry.")
        return redirect
    registry_dict = registry_repository.object_to_dict(registry)
    registry_dict["upload_status"] = "revoked"
    registry_dict["upload_message"] = "Task has been revoked"
    registry_repository.create_by_dict(registry_dict)
    return redirect
