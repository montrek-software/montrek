import os

from django.http import FileResponse, Http404, HttpResponse

from process_pipeline.managers.pipeline_registry_manager import (
    PipelineRegistryManagerABC,
)

from file_export.repositories.file_export_registry_repository import (
    FileExportRegistryRepositoryABC,
)


class FileExportRegistryManagerABC(PipelineRegistryManagerABC):
    repository_class: type[FileExportRegistryRepositoryABC]
    document_name: str = "File Export Registry"
    download_url: str = "under_construction"

    status_attr = "export_status"
    message_attr = "export_message"
    status_column_name = "Export Status"
    message_column_name = "Export Message"
    download_hover_text = "Download export file"

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
