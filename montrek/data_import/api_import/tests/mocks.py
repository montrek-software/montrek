from data_import.api_import.managers.api_data_import_manager import ApiDataImportManager
from data_import.api_import.managers.api_data_import_processor import (
    ApiDataImportProcessorBase,
)
from data_import.api_import.models import (
    MockApiRegistryHub,
    MockApiRegistrySatellite,
)
from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from requesting.managers.request_manager import RequestJsonManager


class MockRequestManager(RequestJsonManager):
    base_url = "https://api.mock.com/v1/"

    def get_response(self, endpoint: str) -> dict:
        self.status_code = 200
        self.message = "request ok"
        return {"some": "data"}


class MockApiDataImportProcessor(ApiDataImportProcessorBase):
    request_manager_class = MockRequestManager
    endpoint = "endpoint"

    def apply_import_data(self) -> bool:
        message = "proccess ok"
        message += self.import_data["some"]
        self.set_message(message)
        return True

    def post_check(self) -> bool:
        return True


class MockApiRegistryRepository(ApiDataImportRegistryRepository):
    registry_satellite = MockApiRegistrySatellite
    hub_class = MockApiRegistryHub


class MockApiDataImportManager(ApiDataImportManager):
    processor_class = MockApiDataImportProcessor
    registry_repository_class = MockApiRegistryRepository


class MockFailedRequestManager(MockRequestManager):
    def get_response(self, endpoint: str) -> dict:
        self.status_code = 0
        self.message = "request error"
        return {}


class MockFailedApiDataImportProcessor(MockApiDataImportProcessor):
    request_manager_class = MockFailedRequestManager


class MockFailedApiDataImportManager(MockApiDataImportManager):
    processor_class = MockFailedApiDataImportProcessor
