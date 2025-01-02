from typing import Any

from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.models import FileUploadRegistryHubABC
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from file_upload.models import (
    FileUploadRegistryHub,
    FileUploadRegistryStaticSatellite,
    LinkFileUploadRegistryFileUploadFile,
)
from montrek.celery_app import SEQUENTIAL_QUEUE_NAME


class MockFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        LinkFileUploadRegistryFileUploadFile
    )


class MockWrongHubClassFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    pass


class MockWrongStaticSatelliteClassFileUploadRegistryRepository(
    FileUploadRegistryRepositoryABC
):
    hub_class = FileUploadRegistryHub


class MockWrongLinkFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite


class MockFileUploadProcessor:
    message: str = "File processed"

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: dict[str, Any],
        **kwargs,
    ):
        pass

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        return True

    def post_check(self, file_path: str) -> bool:
        return True


class MockFileUploadProcessorFail(MockFileUploadProcessor):
    message = "File not processed"

    def process(self, file_path):
        return False


class MockFileUploadProcessorPreCheckFail(MockFileUploadProcessor):
    message = "Pre check failed"

    def pre_check(self, file_path):
        return False


class MockFileUploadProcessorPostCheckFail(MockFileUploadProcessor):
    message = "Post check failed"

    def post_check(self, file_path):
        return False


class MockFileUploadManager(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessor


class MockFileUploadManagerProcessorFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorFail


class MockFileUploadManagerProcessorPreCheckFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorPreCheckFail


class MockFileUploadManagerProcessorPostCheckFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorPostCheckFail


class MockFileUploadManagerSeq(FileUploadManagerABC, task_queue=SEQUENTIAL_QUEUE_NAME):
    file_upload_processor_class = MockFileUploadProcessor
