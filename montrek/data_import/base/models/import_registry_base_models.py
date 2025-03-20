from django.db import models
from baseclasses import models as baseclass_models
from baseclasses.fields import HubForeignKey


class DataImportRegistryBaseSatelliteABC(baseclass_models.MontrekSatelliteABC):
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


class TestRegistryHub(baseclass_models.MontrekHubABC):
    ...


class TestRegistryHubValueDate(baseclass_models.HubValueDate):
    hub = HubForeignKey(TestRegistryHub)


class TestRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    hub_entity = models.ForeignKey(TestRegistryHub, on_delete=models.CASCADE)
