from pathlib import Path

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect

from baseclasses.views import MontrekListView, MontrekTemplateView
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from info.models.download_registry_sat_models import DownloadType
from process_pipeline.views.process_pipeline_view import ProcessPipelineViewABC

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_registry_manager import (
    FileExportRegistryManagerABC,
)


class FileExportTriggerView(ProcessPipelineViewABC):
    manager_class: type[FileExportManagerABC]

    def process(self):
        self.manager.trigger_export()


class FileExportDownloadView(MontrekTemplateView):
    manager_class: type[FileExportRegistryManagerABC]

    def get(self, request, *args, **kwargs):
        export_file = self.manager.repository.get_export_file(
            self.kwargs["pk"], request
        )
        if export_file is None:
            messages.info(request, "No export file available!")
            return redirect(request.META.get("HTTP_REFERER", "/"))
        ext = Path(export_file.name).suffix.lstrip(".").lower()
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType(ext)
        )
        return FileResponse(export_file, as_attachment=True)

    def get_template_context(self, **kwargs):
        return {}


class FileExportRegistryListView(MontrekListView):
    manager_class: type[FileExportRegistryManagerABC]
