from django.db import models

from process_pipeline.models.pipeline_registry_hub_models import PipelineRegistryHubABC
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)


class FileExportRegistryHubABC(PipelineRegistryHubABC):
    class Meta:
        abstract = True


class FileExportRegistryStaticSatelliteABC(PipelineRegistrySatelliteABC):
    class Meta:
        abstract = True

    class ExportStatus(models.TextChoices):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    export_status = models.CharField(
        max_length=20, choices=ExportStatus.choices, default=ExportStatus.PENDING
    )
    export_message = models.TextField(default="")
    export_file = models.FileField(upload_to="file_exports/", null=True, blank=True)
    identifier_fields = ["hub_entity_id"]
