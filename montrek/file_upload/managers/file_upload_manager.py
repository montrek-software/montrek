from typing import TextIO
from typing import Protocol
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class FileUploadProcessorProtocol(Protocol):
    def process(self, file: TextIO) -> bool:
        ...


class FileUploadManager:
    def __init__(
        self, file_upload_processor: FileUploadProcessorProtocol, file: TextIO
    ) -> None:
        self.file_upload_processor = file_upload_processor
        self.repository = FileUploadRegistryRepository()
        self.file = file
        self.file_upload_registry = None

    # def upload(self, file: TextIO) -> None:
    #    self.file_upload_processor.process(file)

    def init_upload(self) -> None:
        file_name = self.file.name
        file_type = file_name.split(".")[-1]
        self.file_upload_registry = self.repository.std_create_object(
            {"file_name": file_name, "file_type": file_type, "upload_status": "pending"}
        )
