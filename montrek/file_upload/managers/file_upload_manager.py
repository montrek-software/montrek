from django.core.files import File
import os
from file_upload.models import FileUploadRegistryHubABC
from django.conf import settings
from typing import Any, Dict
from typing import Protocol

from file_upload.repositories.file_upload_file_repository import (
    FileUploadFileRepository,
)
from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManager,
)
from baseclasses.models import MontrekHubABC
from baseclasses.managers.montrek_manager import MontrekManager
from file_upload.tasks.file_upload_task import FileUploadTask
from montrek.celery_app import PARALLEL_QUEUE_NAME

TASK_SCHEDULED_MESSAGE = "Successfully scheduled background task for processing file. You will receive an email once the task has finished execution."


class FileUploadProcessorProtocol(Protocol):
    message: str

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: Dict[str, Any],
        **kwargs,
    ):
        ...

    def pre_check(self, file_path: str) -> bool:
        ...

    def process(self, file_path: str) -> bool:
        ...

    def post_check(self, file_path: str) -> bool:
        ...


class NotDefinedFileUploadProcessor:
    message = "FileUploadManager needs proper FileUploadProcessor assigned to file_upload_processor_class"

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: Dict[str, Any],
        **kwargs,
    ) -> None:
        raise NotImplementedError(self.message)

    def process(self, file_path: str):
        raise NotImplementedError(self.message)

    def pre_check(self, file_path: str):
        raise NotImplementedError(self.message)

    def post_check(self, file_path: str):
        raise NotImplementedError(self.message)


class FileUploadManagerABC(MontrekManager):
    repository_class = FileUploadFileRepository
    file_upload_processor_class: type[
        FileUploadProcessorProtocol
    ] = NotDefinedFileUploadProcessor
    file_registry_manager_class = FileUploadRegistryManager
    do_process_file_async: bool = True
    process_file_task: FileUploadTask
    message: str

    def __init_subclass__(cls, task_queue: str = PARALLEL_QUEUE_NAME, **kwargs):
        if cls.do_process_file_async:
            cls.process_file_task = FileUploadTask(manager_class=cls, queue=task_queue)

    def __init__(
        self,
        session_data: Dict[str, Any],
    ) -> None:
        super().__init__(session_data=session_data)
        self.registry_manager = self.file_registry_manager_class(session_data)
        self.file_upload_registry: MontrekHubABC | Any = None
        self.file_path = ""
        self.processor: FileUploadProcessorProtocol | None = None
        self.task_id = ""

    def upload_and_process(self, file: File) -> bool:
        # Called by view
        self.session_data["file_upload_registry_id"] = self.register_file_in_db(file)
        if self.do_process_file_async:
            task_result = self.process_file_task.delay(
                session_data=self.session_data,
            )
            self.task_id = task_result.id
            self._load_file_upload_registry()
            self._update_file_upload_registry(celery_task_id=self.task_id)
            result = True
            self.message = TASK_SCHEDULED_MESSAGE
        else:
            result = self.process()
            self.message = self.processor.message
        return result

    def process(self) -> bool:
        # Called by task
        self._load_file_upload_registry()
        self._load_file_path()
        self.processor = self.file_upload_processor_class(
            self.file_upload_registry,
            self.session_data,
        )
        if not self.processor.pre_check(self.file_path):
            self._update_file_upload_registry(
                upload_status="failed", upload_message=self.processor.message
            )
            return False
        if self.processor.process(self.file_path):
            if not self.processor.post_check(self.file_path):
                self._update_file_upload_registry(
                    upload_status="failed", upload_message=self.processor.message
                )
                return False
            self._update_file_upload_registry(
                upload_status="processed", upload_message=self.processor.message
            )
            return True
        else:
            self._update_file_upload_registry(
                upload_status="failed", upload_message=self.processor.message
            )
            return False

    def register_file_in_db(self, file: File) -> int:
        file_name = file.name
        file_type = file_name.split(".")[-1]
        upload_file_hub = self.repository.std_create_object({"file": file})
        file_upload_registry_hub = self.registry_manager.repository.std_create_object(
            {
                "file_name": file_name,
                "file_type": file_type,
                "upload_status": "pending",
                "upload_message": "Upload is pending",
                "link_file_upload_registry_file_upload_file": upload_file_hub,
                "celery_task_id": "",
            }
        )
        return file_upload_registry_hub.pk

    def _update_file_upload_registry(self, **kwargs) -> None:
        att_dict = self.registry_manager.repository.object_to_dict(
            self.file_upload_registry
        )
        att_dict.update(kwargs)
        self.file_upload_registry = self.registry_manager.repository.std_create_object(
            att_dict
        )

    def _load_file_upload_registry(self) -> None:
        file_upload_registry_id = self.session_data["file_upload_registry_id"]
        self.file_upload_registry = self.registry_manager.repository.receive(
            apply_filter=False
        ).get(hub__pk=file_upload_registry_id)

    def _load_file_path(self) -> None:
        self.file_path = os.path.join(
            settings.MEDIA_ROOT,
            self.file_upload_registry.file,
        )
