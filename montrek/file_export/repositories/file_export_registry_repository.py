import os

from django.core.files import File
from django.core.files.storage import default_storage

from process_pipeline.repositories.pipeline_registry_repositories import (
    PipelineRegistryRepositoryABC,
)

from file_export.models import FileExportRegistryStaticSatelliteABC


class FileExportRegistryRepositoryABC(PipelineRegistryRepositoryABC):
    registry_satellite: type[FileExportRegistryStaticSatelliteABC]
    registry_fields = [
        "export_status",
        "export_message",
        "export_file",
    ]

    def get_export_file(self, pk: int, request=None) -> File | None:
        registry = self.receive().get(pk=pk)
        file_path = registry.export_file
        if not file_path:
            return None
        name = str(file_path)
        if not default_storage.exists(name):
            return None
        return File(default_storage.open(name, "rb"), name=os.path.basename(name))
