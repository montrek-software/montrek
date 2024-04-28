from django.db import models

from baseclasses import models as baseclass_models


class ApiUploadRegistryHub(baseclass_models.MontrekHubABC):
    pass


class ApiUploadRegistryStaticSatellite(baseclass_models.MontrekSatelliteABC):
    class UploadStatus(models.TextChoices):
        PENDING = "pending"
        UPLOADED = "uploaded"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    hub_entity = models.ForeignKey(ApiUploadRegistryHub, on_delete=models.CASCADE)
    identifier_fields = ["hub_entity_id"]
    url = models.CharField(max_length=255)
    upload_status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    upload_message = models.TextField(default="")
