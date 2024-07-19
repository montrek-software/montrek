from typing import Any

from file_upload.tasks.process_file_task import ProcessFileTaskABC
from file_upload.models import FileUploadRegistryHubABC
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from file_upload.models import (
    FileUploadRegistryHub,
    FileUploadRegistryStaticSatellite,
    LinkFileUploadRegistryFileUploadFile,
)
from file_upload.managers.background_file_upload_manager import (
    BackgroundFileUploadManagerABC,
)


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


class MockProcessFileTask(ProcessFileTaskABC):
    pass


class MockBackgroundFileUploadManager(BackgroundFileUploadManagerABC):
    repository_class = MockFileUploadRegistryRepository
    file_upload_processor_class = MockFileUploadProcessor
    task = MockProcessFileTask(
        file_upload_processor_class=MockFileUploadProcessor,
        file_upload_registry_repository_class=MockFileUploadRegistryRepository,
    )
