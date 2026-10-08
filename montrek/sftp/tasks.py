from montrek.celery_app import SEQUENTIAL_QUEUE_NAME
from sftp.managers.sftp_import_manager import SftpImportManager
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportSourceRepository,
)
from tasks.montrek_task import MontrekTask


class SftpImportSourceSyncTask(MontrekTask):
    """Poll one import source.

    On the sequential queue, so two polls never import the same file twice:
    a manual "Sync now" and a scheduled poll queue up instead of overlapping.
    """

    def __init__(self):
        super().__init__(queue=SEQUENTIAL_QUEUE_NAME)

    def run(self, source_hub_id: int, user_id: int | None = None) -> str:
        manager = SftpImportManager({"pk": source_hub_id, "user_id": user_id})
        return manager.sync().message


class SftpPollActiveSourcesTask(MontrekTask):
    """Poll every active import source; meant for a Celery Beat schedule.

    Schedule it as a periodic task named
    'sftp.tasks.SftpPollActiveSourcesTask', e.g. every five minutes.
    """

    def __init__(self):
        super().__init__(queue=SEQUENTIAL_QUEUE_NAME)

    def run(self) -> str:
        messages = []
        # Without a user, the managers act as superuser
        source_hub_ids = SftpImportSourceRepository().get_active_source_hub_ids()
        for source_hub_id in source_hub_ids:
            manager = SftpImportManager({"pk": source_hub_id})
            messages.append(f"{source_hub_id}: {manager.sync().message}")
        return "\n".join(messages) or "No active SFTP import sources"


sftp_import_source_sync_task = SftpImportSourceSyncTask()
sftp_poll_active_sources_task = SftpPollActiveSourcesTask()
