import logging

from typing import Any, Dict
from company.tasks.rgs import process_rgs_file_task

logger = logging.getLogger(__name__)


class CompanyFileUploadProcessor:
    message = "Not implemented"
    file_upload_registry = None

    def __init__(
        self, file_upload_registry_id: int, session_data: Dict[str, Any], **kwargs
    ):
        self.session_data = session_data
        self.file_upload_registry_id = file_upload_registry_id

    def process(self, file_path: str):
        result = process_rgs_file_task.delay(
            file_path=file_path,
            session_data=self.session_data,
            file_upload_registry_id=self.file_upload_registry_id,
        )
        logger.info(f"Upload task started with id {result.id}.")
        self.message = "Upload background task started. You will receive an email when the task is finished."
        return True

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True
