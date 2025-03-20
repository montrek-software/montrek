from django.db import models
from baseclasses import models as baseclass_models


class DataImportRegistryBaseSatelliteABC(baseclass_models.MontrekSatelliteABC):
    class Meta:
        abstract = True

    class UploadStatus(models.TextChoices):
        PENDING = "pending"
        UPLOADED = "uploaded"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    upload_status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    upload_message = models.TextField(default="")
    identifier_fields = ["hub_entity_id"]
