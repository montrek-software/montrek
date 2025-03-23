from data_import.base.managers.data_import_managers import DataImportManagerABC
from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)


class ApiDataImportManager(DataImportManagerABC):
    registry_repository_class = ApiDataImportRegistryRepository
