from abc import abstractmethod
from typing import Any
from baseclasses.managers.montrek_manager import MontrekManager

ImportDataType = dict[str, Any]


class DataImportManagerABC(MontrekManager):
    def __init__(self, session_data: dict[str, Any]):
        super().__init__(session_data)
        self.import_data: None | ImportDataType = None

    def set_import_data(self, import_data: ImportDataType):
        raise NotImplementedError(
            f"Implement 'set_import_data' method in {self.__class__.__name__}"
        )
