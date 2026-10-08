from baseclasses.dataclasses.montrek_message import MontrekMessageInfo
from baseclasses.managers.montrek_manager import MontrekManager
from sftp.tasks import sftp_import_source_sync_task

SYNC_SCHEDULED_MESSAGE = (
    "Sync scheduled. New files show up under the source's imported files and "
    "in the registry of its upload pipeline."
)


class SftpImportSchedulerManager(MontrekManager):
    """Queue a poll of the import source in session_data["pk"] (its hub id)."""

    def schedule_sync(self) -> None:
        sftp_import_source_sync_task.delay(
            source_hub_id=self.session_data["pk"],
            user_id=self.session_data.get("user_id"),
        )
        self.messages.append(MontrekMessageInfo(SYNC_SCHEDULED_MESSAGE))
