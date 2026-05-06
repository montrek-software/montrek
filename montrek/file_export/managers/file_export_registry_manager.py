from reporting.dataclasses.table_elements import (
    DateTimeTableElement,
    LinkTableElement,
    StringTableElement,
    TextTableElement,
)
from reporting.managers.montrek_table_manager import MontrekTableManager

from file_export.repositories.file_export_registry_repository import (
    FileExportRegistryRepositoryABC,
)


class FileExportRegistryManagerABC(MontrekTableManager):
    repository_class: type[FileExportRegistryRepositoryABC]
    document_name: str = "File Export Registry"
    download_url: str = "under_construction"

    @property
    def table_elements(self) -> tuple:
        return (
            DateTimeTableElement(name="Created At", attr="created_at"),
            StringTableElement(name="Export Status", attr="export_status"),
            TextTableElement(name="Export Message", attr="export_message"),
            LinkTableElement(
                name="Download",
                url=self.download_url,
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download export file",
            ),
        )
