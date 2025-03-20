from data_import.base.managers.data_import_managers import (
    DataImportManagerABC,
    ImportDataType,
)
from data_import.base.models.import_registry_base_models import (
    TestRegistryHub,
    TestRegistrySatellite,
)
from data_import.base.repositories.registry_repositories import RegistryRepositoryABC


class MockRegistryRepository(RegistryRepositoryABC):
    registry_satellite = TestRegistrySatellite
    hub_class = TestRegistryHub


class MockDataImportManager(DataImportManagerABC):
    registry_repository_class = MockRegistryRepository

    def set_import_data(self, import_data: ImportDataType):
        self.import_data = import_data
