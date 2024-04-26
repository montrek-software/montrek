from django.db import models

from baseclasses import models as baseclass_models


class ApiUploadRegistryHub(baseclass_models.MontrekHubABC):
    pass
    # link_api_upload_registry_api_upload_response = models.ManyToManyField(
    #     "api_upload.ApiUploadResponseHub",
    #     related_name="link_api_upload_response_api_upload_registry",
    #     through="LinkApiUploadRegistryApiUploadResponse",
    # )


# class LinkApiUploadRegistryApiUploadResponse(baseclass_models.MontrekOneToOneLinkABC):
#     hub_in = models.ForeignKey(
#         "api_upload.ApiUploadRegistryHub", on_delete=models.CASCADE
#     )
#     hub_out = models.ForeignKey(
#         "api_upload.ApiUploadResponseHub", on_delete=models.CASCADE
#     )


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


#
# class ApiUploadResponseHub(baseclass_models.MontrekHubABC):
#     pass
#
#
# class ApiUploadResponseStaticSatellite(baseclass_models.MontrekSatelliteABC):
#     hub_entity = models.ForeignKey(ApiUploadResponseHub, on_delete=models.CASCADE)
#     identifier_fields = ["hub_entity_id"]
#     content = models.TextField
