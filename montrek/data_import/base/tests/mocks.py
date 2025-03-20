from data_import.base.managers.data_import_managers import (
    DataImportManagerABC,
    ImportDataType,
)


class MockDataImportManager(DataImportManagerABC):
    def set_import_data(self, import_data: ImportDataType):
        self.import_data = import_data
