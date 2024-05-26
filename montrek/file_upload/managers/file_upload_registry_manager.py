from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
    FileUploadRegistryRepository,
)
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.dataclasses.table_elements import (
    DateTableElement,
    LinkTableElement,
    StringTableElement,
)


class FileUploadRegistryManagerABC(MontrekTableManager):
    repository_class = FileUploadRegistryRepositoryABC

    @property
    def table_elements(self) -> tuple:
        return (
            StringTableElement(name="File Name", attr="file_name"),
            StringTableElement(name="Upload Status", attr="upload_status"),
            StringTableElement(name="Upload Message", attr="upload_message"),
            DateTableElement(name="Upload Date", attr="created_at"),
            StringTableElement(name="Uploaded By", attr="created_by"),
            LinkTableElement(
                name="File",
                url="montrek_download_file",
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download",
            ),
        )


class FileUploadRegistryManager(FileUploadRegistryManagerABC):
    repository_class = FileUploadRegistryRepository
