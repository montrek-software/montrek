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


class MockRegistryRepository(RegistryRepositoryABC):
    registry_satellite = TestRegistrySatellite
    hub_class = TestRegistryHub


class MockProcessor(ProcessorBaseABC):
    def process(self) -> bool:
        self.set_message("Sucessfull Import")
        return True


class MockDataImportManager(DataImportManagerABC):
    registry_repository_class = MockRegistryRepository
    processor_class = MockProcessor

    def set_import_data(self, import_data: ImportDataType):
        self.import_data = import_data
