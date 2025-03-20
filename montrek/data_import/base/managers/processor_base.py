from typing import Any
from data_import.types import ImportDataType


class ProcessorBaseABC:
    def __init__(self, session_data: dict[str, Any], import_data: ImportDataType):
        self.session_data = session_data
        self.import_data = import_data
        self._message = ""

    def process(self) -> bool:
        raise NotImplementedError(f"Set 'process' Method in {self.__class__.__name__}")

    def pre_check(self) -> bool:
        raise NotImplementedError(
            f"Set 'pre_check' Method in {self.__class__.__name__}"
        )

    def set_message(self, message: str):
        self._message = message

    def get_message(self) -> str:
        return self._message
