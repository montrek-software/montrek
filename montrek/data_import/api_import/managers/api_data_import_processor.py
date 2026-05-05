from typing import Any
from data_import.base.managers.processor_base import ProcessorBaseABC
from data_import.types import ImportDataType
from requesting.managers.request_manager import RequestManagerABC


class ApiDataImportProcessorBase(ProcessorBaseABC):
    request_manager_class: type[RequestManagerABC]

    def __init__(self, session_data: dict[str, Any], import_data: ImportDataType):
        super().__init__(session_data, import_data)
        self.request_manager = self.request_manager_class(session_data)

    def get_endpoint_url(self, endpoint: str) -> str:
        return self.request_manager.get_endpoint_url(endpoint)
