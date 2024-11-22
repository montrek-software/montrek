from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.tasks.process_file_task import ProcessFileTaskABC


class BackgroundFileUploadManagerABC(FileUploadManagerABC):
    task = type[ProcessFileTaskABC]

    def upload_and_process(self) -> bool:
        self.processor.message = "Upload background task scheduled. You will receive an email when the task is finished."
        self.update_file_upload_registry("scheduled", self.processor.message)
        self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.file_upload_registry.id,
            session_data=self.session_data,
        )
        return True
