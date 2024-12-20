import os
from file_upload.models import FileUploadRegistryHubABC
from django.conf import settings
from typing import Any, TextIO, Dict
from typing import Protocol

from file_upload.repositories.file_upload_file_repository import (
    FileUploadFileRepository,
)
from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManager,
)
from baseclasses.models import MontrekHubABC
from baseclasses.managers.montrek_manager import MontrekManager
from tasks.montrek_task import MontrekTask


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

    def process(self, file: TextIO):
        raise NotImplementedError(self.message)

    def pre_check(self, file: TextIO):
        raise NotImplementedError(self.message)

    def post_check(self, file: TextIO):
        raise NotImplementedError(self.message)


class FileUploadTask(MontrekTask):
    def __init__(
        self,
        manager_class: type[MontrekManager],
    ):
        self.manager_class = manager_class
        task_name = (
            f"{manager_class.__module__}.{manager_class.__name__}_process_file_task"
        )
        super().__init__(task_name)

    def run(self, session_data: Dict[str, Any]):
        manager = self.manager_class(session_data)
        manager.process()
        message = manager.processor.message
        return message


class FileUploadManagerABC(MontrekManager):
    repository_class = FileUploadFileRepository
    file_upload_processor_class: type[
        FileUploadProcessorProtocol
    ] = NotDefinedFileUploadProcessor
    file_registry_manager_class = FileUploadRegistryManager
    process_file_task: FileUploadTask

    def __init_subclass__(cls, **kwargs):
        cls.process_file_task = FileUploadTask(manager_class=cls)

    def __init__(
        self,
        session_data: Dict[str, Any],
        **kwargs,
    ) -> None:
        super().__init__(session_data=session_data)
        self.registry_manager = self.file_registry_manager_class(session_data)
        self.file_upload_registry: MontrekHubABC | Any = None
        self.file_path = ""

    def upload_and_process(self, file: TextIO | None) -> bool:
        # Called by view
        self.session_data["file_upload_registry_id"] = self._register_file_in_db(file)
        self.process_file_task.delay(
            session_data=self.session_data,
        )
        return True

    def process(self) -> bool:
        # Called by task
        self._load_file_upload_registry()
        self._load_file_path()
        self.processor = self.file_upload_processor_class(
            self.file_upload_registry,
            self.session_data,
        )
        if not self.processor.pre_check(self.file_path):
            self._update_file_upload_registry("failed", self.processor.message)
            return False
        if self.processor.process(self.file_path):
            if not self.processor.post_check(self.file_path):
                self._update_file_upload_registry("failed", self.processor.message)
                return False
            self._update_file_upload_registry("processed", self.processor.message)
            return True
        else:
            self._update_file_upload_registry("failed", self.processor.message)
            return False

    def _register_file_in_db(self, file: TextIO) -> int:
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
            }
        )
        return file_upload_registry_hub.pk

    def _update_file_upload_registry(
        self, upload_status: str, upload_message: str
    ) -> None:
        att_dict = self.registry_manager.repository.object_to_dict(
            self.file_upload_registry
        )
        att_dict.update(
            {
                "upload_status": upload_status,
                "upload_message": upload_message,
            },
        )
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
