from data_import.base.managers.data_import_managers import (
    DataImportManagerABC,
    ImportDataType,
)
from data_import.base.managers.processor_base import ProcessorBaseABC
from data_import.base.models.import_registry_base_models import (
    TestRegistryHub,
    TestRegistrySatellite,
)
from data_import.base.repositories.registry_repositories import RegistryRepositoryABC
from data_import.base.tasks.data_import_task import DataImportTask


class MockRegistryRepository(RegistryRepositoryABC):
    registry_satellite = TestRegistrySatellite
    hub_class = TestRegistryHub


class MockProcessor(ProcessorBaseABC):
    def process(self) -> bool:
        self.set_message("Sucessfull Import")
        return True

    def pre_check(self) -> bool:
        return True

    def post_check(self) -> bool:
        return True


class MockProcessorFailPreCheck(MockProcessor):
    def pre_check(self) -> bool:
        self.set_message("Pre Check Failed")
        return False


class MockProcessorFailPostCheck(MockProcessor):
    def post_check(self) -> bool:
        self.set_message("Post Check Failed")
        return False


class MockProcessorFailProcess(MockProcessor):
    def process(self) -> bool:
        self.set_message("Process Failed")
        return False


class MockDataImportManager(DataImportManagerABC):
    registry_repository_class = MockRegistryRepository
    processor_class = MockProcessor

    def set_import_data(self, import_data: ImportDataType):
        self.import_data = import_data


class MockDataImportManagerFailPreCheck(MockDataImportManager):
    processor_class = MockProcessorFailPreCheck


class MockDataImportManagerFailPostCheck(MockDataImportManager):
    processor_class = MockProcessorFailPostCheck


class MockDataImportManagerFailProcess(MockDataImportManager):
    processor_class = MockProcessorFailProcess


class MockDataImportTask(DataImportTask):
    manager_class = MockDataImportManager
    success_subject = "Data Import Task successful"
