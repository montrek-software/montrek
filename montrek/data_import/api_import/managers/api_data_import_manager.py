from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from data_import.base.managers.data_import_managers import DataImportManagerABC
from requesting.managers.request_manager import RequestManagerABC


class ApiDataImportManager(DataImportManagerABC):
    registry_repository_class = ApiDataImportRegistryRepository
    request_processor_class: type[RequestManagerABC] | None = None
    endpoint: str = ""

    def additional_registry_data(self) -> dict:
        return {"import_url": self.processor.get_endpoint_url(self.endpoint)}
