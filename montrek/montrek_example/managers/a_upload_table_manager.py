from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManagerABC,
)
from reporting.dataclasses.table_elements import (
    DateTimeTableElement,
    StringTableElement,
)
from montrek_example.repositories.hub_a_repository import (
    HubAUploadRepository,
    HubAFileUploadRegistryRepository,
)
from reporting.managers.montrek_table_manager import MontrekTableManager


class HubAUploadTableManager(MontrekTableManager):
    repository_class = HubAUploadRepository

    @property
    def table_elements(self):
        return (
            StringTableElement(name="url", attr="url"),
            StringTableElement(name="upload_status", attr="upload_status"),
            StringTableElement(name="upload_message", attr="upload_message"),
            DateTimeTableElement(name="created_at", attr="created_at"),
        )


class HubAFileUploadRegistryManager(FileUploadRegistryManagerABC):
    repository_class = HubAFileUploadRegistryRepository
