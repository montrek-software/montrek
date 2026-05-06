import io

import pandas as pd
from django.core.files.base import ContentFile

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_processor_abc import FileExportProcessorABC
from file_export.managers.file_export_registry_manager import (
    FileExportRegistryManagerABC,
)
from montrek_example.models.example_models import HubA
from montrek_example.repositories.hub_a_repository import (
    HubAFileExportRegistryRepository,
)


class HubAFileExportProcessor(FileExportProcessorABC):
    def pre_check(self) -> bool:
        self._count = HubA.objects.count()
        if self._count == 0:
            self.set_message("No HubA records found for export.")
            return False
        return True

    def process(self) -> bool:
        try:
            hub_ids = list(HubA.objects.values_list("id", flat=True))
            df = pd.DataFrame({"hub_id": hub_ids})
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            self.set_result_file(
                ContentFile(buffer.getvalue(), name="hub_a_export.csv")
            )
            self.set_message(f"Exported {self._count} records.")
        except Exception as exc:  # noqa: BLE001
            self.set_message(f"Export failed: {exc}")
            return False
        return True

    def post_check(self) -> bool:
        return self.result_file is not None


class HubAFileExportManager(FileExportManagerABC):
    registry_repository_class = HubAFileExportRegistryRepository
    processor_class = HubAFileExportProcessor
    do_process_async = False


class HubAFileExportRegistryManager(FileExportRegistryManagerABC):
    repository_class = HubAFileExportRegistryRepository
    document_name = "Hub A File Export Registry"
    download_url = "hub_a_file_export_download"
