import datetime

from montrek.celery_app import FAST_QUEUE_NAME
from reporting.constants import LATEX_PDF_STORAGE_DIR
from reporting.modules.mailed_downloads import MailedDownloads
from storage.modules.storage_cleanup import StorageCleanup
from tasks.montrek_task import MontrekTask

# Mailed table links and the PDFs attached to a mail draft are both meant to be
# used within days; whatever is left after a week is not picked up any more.
MAX_AGE = datetime.timedelta(days=7)


class ReportingStorageCleanupTask(MontrekTask):
    """Delete mailed tables and report PDFs older than MAX_AGE.

    Scheduled daily by migration reporting.0001.
    """

    def __init__(self):
        super().__init__(queue=FAST_QUEUE_NAME)

    def run(self) -> str:
        deleted = sum(
            StorageCleanup(directory, MAX_AGE).delete_old_files()
            for directory in (MailedDownloads.STORAGE_DIR, LATEX_PDF_STORAGE_DIR)
        )
        return f"Deleted {deleted} files"


reporting_storage_cleanup_task = ReportingStorageCleanupTask()
