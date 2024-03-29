import os
from django.conf import settings
from django.db import models

from baseclasses import models as baseclass_models

# Create your models here.


class FileUploadRegistryHub(baseclass_models.MontrekHubABC):
    link_file_upload_registry_file_upload_file = models.ManyToManyField(
        "file_upload.FileUploadFileHub",
        related_name="link_file_upload_file_file_upload_registry",
        through="LinkFileUploadRegistryFileUploadFile",
    )


class LinkFileUploadRegistryFileUploadFile(baseclass_models.MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(
        "file_upload.FileUploadRegistryHub", on_delete=models.CASCADE
    )
    hub_out = models.ForeignKey(
        "file_upload.FileUploadFileHub", on_delete=models.CASCADE
    )


class FileUploadRegistryStaticSatellite(baseclass_models.MontrekSatelliteABC):
    class FileTypes(models.TextChoices):
        CSV = "csv"
        JSON = "json"
        XML = "xml"
        XLSX = "xlsx"
        XLS = "xls"
        TXT = "txt"
        NONE = "none"

    class UploadStatus(models.TextChoices):
        PENDING = "pending"
        UPLOADED = "uploaded"
        IN_PROGRESS = "in_progress"
        PROCESSED = "processed"
        FAILED = "failed"

    hub_entity = models.ForeignKey(FileUploadRegistryHub, on_delete=models.CASCADE)
    identifier_fields = ["file_name", "file_type"]
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=5, choices=FileTypes.choices, default=FileTypes.NONE
    )
    upload_status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    upload_message = models.TextField(default="")

    def clean(self):
        super().clean()
        if self.file_type == self.FileTypes.NONE:
            raise IOError(f'File "{self.file_name}" has no file type')
        if self.file_type not in self.FileTypes.values:
            raise IOError(f'File type "{self.file_type}" is not valid')

    def save(self, *args, **kwargs):
        if self.file_type == self.FileTypes.NONE and "." in self.file_name:
            self.file_type = self.file_name.split(".")[-1]
        self.clean()
        super().save(*args, **kwargs)


class FileUploadFileHub(baseclass_models.MontrekHubABC):
    pass


class FileUploadFileStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(FileUploadFileHub, on_delete=models.CASCADE)
    identifier_fields = ["hub_entity_id"]
    file = models.FileField()


class FieldMapHub(baseclass_models.MontrekHubABC):
    pass


class FieldMapStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(FieldMapHub, on_delete=models.CASCADE)
    identifier_fields = ["hub_entity_id"]

    source_field = models.CharField(max_length=255)
    database_field = models.CharField(max_length=255)
