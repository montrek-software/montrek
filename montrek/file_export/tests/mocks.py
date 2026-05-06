from django.core.files.base import ContentFile

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_processor_abc import FileExportProcessorABC
from file_export.managers.file_export_registry_manager import (
    FileExportRegistryManagerABC,
)
from file_export.models import (
    TestFileExportRegistryHub,
    TestFileExportRegistryStaticSatellite,
)
from file_export.repositories.file_export_registry_repository import (
    FileExportRegistryRepositoryABC,
)


class MockFileExportRegistryRepository(FileExportRegistryRepositoryABC):
    hub_class = TestFileExportRegistryHub
    registry_satellite = TestFileExportRegistryStaticSatellite


class MockFileExportProcessor(FileExportProcessorABC):
    def pre_check(self) -> bool:
        return True

    def process(self) -> bool:
        self.set_result_file(ContentFile(b"col1,col2\n1,2\n", name="export.csv"))
        self.set_message("Export successful")
        return True

    def post_check(self) -> bool:
        return self.result_file is not None


class MockFileExportProcessorFailPreCheck(MockFileExportProcessor):
    def pre_check(self) -> bool:
        self.set_message("Pre Check Failed")
        return False


class MockFileExportProcessorFailProcess(MockFileExportProcessor):
    def process(self) -> bool:
        self.set_message("Process Failed")
        return False


class MockFileExportProcessorFailPostCheck(MockFileExportProcessor):
    def post_check(self) -> bool:
        self.set_message("Post Check Failed")
        return False


class MockFileExportProcessorNoFile(MockFileExportProcessor):
    def process(self) -> bool:
        self.set_message("No file generated")
        return True

    def post_check(self) -> bool:
        return True


class MockFileExportManager(FileExportManagerABC):
    registry_repository_class = MockFileExportRegistryRepository
    processor_class = MockFileExportProcessor
    do_process_async = False


class MockFileExportManagerFailPreCheck(MockFileExportManager):
    processor_class = MockFileExportProcessorFailPreCheck


class MockFileExportManagerFailProcess(MockFileExportManager):
    processor_class = MockFileExportProcessorFailProcess


class MockFileExportManagerFailPostCheck(MockFileExportManager):
    processor_class = MockFileExportProcessorFailPostCheck


class MockFileExportManagerNoFile(MockFileExportManager):
    processor_class = MockFileExportProcessorNoFile


class MockFileExportRegistryManager(FileExportRegistryManagerABC):
    repository_class = MockFileExportRegistryRepository
    document_name = "Test Export"
    download_url = "under_construction"
