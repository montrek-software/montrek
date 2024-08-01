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
    download_url = "please define download_url in subclass"
    download_log_url = ""
    history_url = ""

    @property
    def table_elements(self) -> tuple:
        table_elements = [
            StringTableElement(name="File Name", attr="file_name"),
            StringTableElement(name="Upload Status", attr="upload_status"),
            StringTableElement(name="Upload Message", attr="upload_message"),
            DateTableElement(name="Upload Date", attr="upload_date"),
            StringTableElement(name="Uploaded By", attr="created_by"),
            LinkTableElement(
                name="File",
                url=self.download_url,
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download",
            ),
        ]
        if self.download_log_url != "":
            table_elements.append(
                LinkTableElement(
                    name="Log",
                    url=self.download_log_url,
                    kwargs={"pk": "id"},
                    icon="download",
                    hover_text="Download Log",
                )
            )
        if self.history_url != "":
            table_elements.append(
                LinkTableElement(
                    name="History",
                    url=self.history_url,
                    kwargs={"pk": "id"},
                    icon="road",
                    hover_text="History",
                )
            )
        return tuple(table_elements)


class FileUploadRegistryManager(FileUploadRegistryManagerABC):
    repository_class = FileUploadRegistryRepository
