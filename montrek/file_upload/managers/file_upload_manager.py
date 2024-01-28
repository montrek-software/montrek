from typing import TextIO
from typing import Protocol


class FileUploadProcessorProtocol(Protocol):
    def process(self, file: TextIO) -> None:
        ...


class FileUploadManager:
    def __init__(
        self, file_upload_processor: FileUploadProcessorProtocol, file_path: str
    ) -> None:
        self.file_upload_processor = file_upload_processor

    # def upload(self, file: TextIO) -> None:
    #    self.file_upload_processor.process(file)
