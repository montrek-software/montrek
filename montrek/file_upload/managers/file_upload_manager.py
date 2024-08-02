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


class FileUploadManagerABC(MontrekManager):
    repository_class = FileUploadFileRepository
    file_upload_processor_class: type[
        FileUploadProcessorProtocol
    ] = NotDefinedFileUploadProcessor
    file_registry_manager_class = FileUploadRegistryManager

    def __init__(
        self,
        file: TextIO,
        session_data: Dict[str, Any],
        **kwargs,
    ) -> None:
        super().__init__(session_data=session_data)
        self.registry_manager = self.file_registry_manager_class(session_data)
        self.file = file
        self.file_upload_registry: MontrekHubABC | Any = None
        self.file_path = ""
        self.init_upload()
        self.processor = self.file_upload_processor_class(
            self.file_upload_registry, session_data, **kwargs
        )

    def upload_and_process(self) -> bool:
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

    def init_upload(self) -> None:
        file_name = self.file.name
        file_type = file_name.split(".")[-1]
        upload_file_hub = self.repository.std_create_object({"file": self.file})
        self.file_path = os.path.join(
            settings.MEDIA_ROOT,
            self.repository.std_queryset().get(pk=upload_file_hub.pk).file,
        )
        file_upload_registry_hub = self.registry_manager.repository.std_create_object(
            {
                "file_name": file_name,
                "file_type": file_type,
                "upload_status": "pending",
                "upload_message": "Upload is pending",
                "link_file_upload_registry_file_upload_file": upload_file_hub,
            }
        )
        self.file_upload_registry = self.registry_manager.repository.std_queryset().get(
            pk=file_upload_registry_hub.pk
        )

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
