from data_import.api_import.managers.api_data_import_processor import (
    ApiDataImportProcessorBase,
)
from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from data_import.base.managers.data_import_managers import DataImportManagerABC


class ApiDataImportManager(DataImportManagerABC):
    registry_repository_class = ApiDataImportRegistryRepository
    processor_class: type[ApiDataImportProcessorBase]

    def additional_registry_data(self) -> dict:
        return {"import_url": self.processor.get_endpoint_url(self.endpoint)}
