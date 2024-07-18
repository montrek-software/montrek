from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.tasks.process_file_task import ProcessFileTaskBase


class BackgroundFileUploadManagerABC(FileUploadManagerABC):
    task = type[ProcessFileTaskBase]

    def upload_and_process(self) -> bool:
        if not self.processor.pre_check(self.file_path):
            self._update_file_upload_registry("failed", self.processor.message)
            return False
        self.processor.message = "Upload background task scheduled. You will receive an email when the task is finished."
        self._update_file_upload_registry("scheduled", self.processor.message)
        self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.file_upload_registry.id,
            session_data=self.session_data,
        )
        return True
