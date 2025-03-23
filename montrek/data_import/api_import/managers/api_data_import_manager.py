from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from data_import.base.managers.data_import_managers import DataImportManagerABC
from data_import.types import ImportDataType
from requesting.managers.request_manager import RequestManagerABC


class ApiDataImportManager(DataImportManagerABC):
    registry_repository_class = ApiDataImportRegistryRepository
    request_manager_class: type[RequestManagerABC] | None = None
    endpoint: str = ""

    def __init__(self, session_data: dict):
        if not self.request_manager_class:
            raise NotImplementedError(
                f"Set 'request_manager_class' attribute in {self.__class__.__name__}"
            )
        self.request_manager = self.request_manager_class(session_data)
        super().__init__(session_data)

    def process_import_data(self, import_data: ImportDataType = {}):
        response = self.request_manager.get_response(self.endpoint)
        return super().process_import_data(response)

    def additional_registry_data(self) -> dict:
        return {"import_url": self.request_manager.get_endpoint_url(self.endpoint)}
