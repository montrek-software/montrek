import os

from django.http import FileResponse, Http404, HttpResponse

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

    def download(self) -> HttpResponse:
        pk = int(self.session_data["pk"])
        export_file = self.repository.get_export_file(pk)
        if export_file is None:
            raise Http404("Export file not found.")
        return FileResponse(export_file)

    def get_filename(self) -> str:
        pk = int(self.session_data["pk"])
        registry = self.repository.receive().get(pk=pk)
        file_path = registry.export_file
        if not file_path:
            return "export.csv"
        return os.path.basename(str(file_path))
