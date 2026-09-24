from __future__ import annotations

from typing import TYPE_CHECKING

from tasks.montrek_task import MontrekTask

if TYPE_CHECKING:
    # Runtime import would be circular: the table manager creates this task.
    from reporting.managers.montrek_table_manager import MontrekTableManagerABC


class DownloadTableTask(MontrekTask):
    def __init__(self, manager_class: type[MontrekTableManagerABC]):
        self.manager_class = manager_class
        task_name = f"{manager_class.__module__}.{manager_class.__name__}_download_task"
        super().__init__(task_name)

    def run(self, filetype, session_data: dict) -> str:
        self.manager_class(session_data).send_table_by_mail(filetype)
        return "Table sent by mail."
