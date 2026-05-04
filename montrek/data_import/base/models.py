from django.db import models
from baseclasses import models as baseclass_models
from baseclasses.fields import HubForeignKey
from process_pipeline.models.pipeline_registry_hub_models import PipelineRegistryHubABC
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)


class DataImportRegistryBaseSatelliteABC(PipelineRegistrySatelliteABC):
    class Meta:
        abstract = True

    class ImportStatus(models.TextChoices):
        PENDING = "pending"
        UPLOADED = "uploaded"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    import_status = models.CharField(
        max_length=20, choices=ImportStatus.choices, default=ImportStatus.PENDING
    )
    import_message = models.TextField(default="")
    identifier_fields = ["hub_entity_id"]


class TestRegistryHub(PipelineRegistryHubABC): ...


class TestRegistryHubValueDate(baseclass_models.HubValueDate):
    hub = HubForeignKey(TestRegistryHub)


class TestRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    hub_entity = models.ForeignKey(TestRegistryHub, on_delete=models.CASCADE)
