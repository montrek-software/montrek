from django.db import models

from baseclasses import models as baseclass_models


class ApiUploadRegistryHubABC(baseclass_models.MontrekHubABC):
    class Meta:
        abstract = True


class ApiUploadRegistryStaticSatelliteABC(baseclass_models.MontrekSatelliteABC):
    class Meta:
        abstract = True

    class UploadStatus(models.TextChoices):
        PENDING = "pending"
        UPLOADED = "uploaded"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    hub_entity = models.ForeignKey(ApiUploadRegistryHubABC, on_delete=models.CASCADE)
    identifier_fields = ["hub_entity_id"]
    url = models.CharField(max_length=255)
    upload_status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    upload_message = models.TextField(default="")


class ApiUploadRegistryHub(ApiUploadRegistryHubABC):
    pass


class ApiUploadRegistryStaticSatellite(ApiUploadRegistryStaticSatelliteABC):
    hub_entity = models.ForeignKey(ApiUploadRegistryHub, on_delete=models.CASCADE)
