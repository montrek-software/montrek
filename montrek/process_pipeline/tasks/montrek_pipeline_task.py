from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from process_pipeline.managers.montrek_pipeline_managers import (
        MontrekPipelineManagerABC,
    )

from django.contrib.auth import get_user_model
from mailing.managers.mailing_manager import MailingManager
from tasks.montrek_task import MontrekTask
from user.models import MontrekUser

from montrek.celery_app import PARALLEL_QUEUE_NAME


class MontrekPipelineTask(MontrekTask):
    mailing_manager_class: type[MailingManager] = MailingManager

    def __init__(
        self,
        manager_class: type[MontrekPipelineManagerABC],
        queue: str = PARALLEL_QUEUE_NAME,
    ):
        self.manager_class = manager_class
        task_name = f"{manager_class.__module__}.{manager_class.__name__}_pipeline_task"
        super().__init__(task_name, queue)

    def run(
        self, session_data: dict[str, Any], pipeline_data: dict[str, Any] | None = None
    ) -> str:
        if pipeline_data is None:
            pipeline_data = {}
        manager = self.manager_class(session_data)
        result = manager.process(pipeline_data=pipeline_data)
        self._send_result_mail(manager, session_data, result)
        return manager.message

    def recipients(self, session_data: dict[str, Any]) -> list[MontrekUser]:
        return [get_user_model().objects.get(pk=session_data["user_id"])]

    def _send_result_mail(
        self,
        manager: MontrekPipelineManagerABC,
        session_data: dict[str, Any],
        result: bool,
    ) -> None:
        self.mailing_manager_class(session_data=session_data).send_montrek_mail(
            ",".join(str(r.email) for r in self.recipients(session_data)),
            self._get_subject(result),
            manager.message,
        )

    def _message_name(self) -> str:
        return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", self.manager_class.__name__)

    def _get_subject(self, result: bool) -> str:
        name = self._message_name()
        return f"{name} successful" if result else f"ERROR: {name} unsuccessful"
