from baseclasses.views import MontrekDownloadView, MontrekListView
from process_pipeline.views.process_pipeline_view import ProcessPipelineViewABC

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_registry_manager import (
    FileExportRegistryManagerABC,
)


class FileExportTriggerView(ProcessPipelineViewABC):
    manager_class: type[FileExportManagerABC]

    def process(self):
        self.manager.trigger_export()


class FileExportDownloadView(MontrekDownloadView):
    manager_class: type[FileExportRegistryManagerABC]


class FileExportRegistryListView(MontrekListView):
    manager_class: type[FileExportRegistryManagerABC]
