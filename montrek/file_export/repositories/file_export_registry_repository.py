import os

from django.conf import settings
from django.core.files import File

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
        full_path = os.path.join(settings.MEDIA_ROOT, str(file_path))
        if not os.path.exists(full_path):
            return None
        return File(
            open(full_path, "rb"),  # noqa: SIM115
            name=os.path.basename(full_path),
        )
