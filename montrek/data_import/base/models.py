from django.db import models
from data_import.base.constants import ImportStatus
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)


class DataImportRegistryBaseSatelliteABC(PipelineRegistrySatelliteABC):
    class Meta:
        abstract = True

    import_status = models.CharField(
        max_length=20,
        choices=ImportStatus.to_list(),
        default=ImportStatus.PENDING.value.label,
    )
    import_message = models.TextField(default="")
    identifier_fields = ["hub_entity_id"]
