from typing import Any
from data_import.base.managers.processor_base import ProcessorBaseABC
from data_import.types import ImportDataType
from requesting.managers.request_manager import RequestManagerABC


class ApiDataImportProcessorBase(ProcessorBaseABC):
    request_manager_class: type[RequestManagerABC]
    endpoint: str

    def __init__(self, session_data: dict[str, Any], import_data: ImportDataType):
        super().__init__(session_data, import_data)
        self.request_manager = self.request_manager_class(session_data)
        self.import_data = None

    def pre_check(self) -> bool:
        self._read_import_data()
        if self.request_manager.status_code != 200:
            self.message = self.request_manager.message
            return False
        return True

    def process(self) -> bool:
        return self.process_import_data()

    def _read_import_data(self):
        self.import_data = self.request_manager.get_response(self.endpoint)

    def process_import_data(self):
        raise NotImplementedError(
            f"Add process_import_data method for {self.__class__.__name__}"
        )

    def get_endpoint_url(self) -> str:
        return self.request_manager.get_endpoint_url(self.endpoint)
