import re

from django.db import models

from baseclasses import models as baseclass_models
# Create your models here.

class FileUploadRegistryHub(baseclass_models.MontrekHubABC):
    pass

class FileUploadRegistryStaticSatellite(baseclass_models.MontrekSatelliteABC):
    class FileTypes(models.TextChoices):
        CSV = 'csv'
        JSON = 'json'
        XML = 'xml'
        XLSX = 'xlsx'
        XLS = 'xls'
        TXT = 'txt'
        NONE = 'none'

    class UploadStatus(models.TextChoices):
        PENDING = 'pending'
        UPLOADED = 'uploaded'
        IN_PROGRESS = 'in_progress'
        PROCESSED = 'processed'
        FAILED = 'failed'

    hub_entity = models.ForeignKey(FileUploadRegistryHub, 
                                   on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    file_type = models.CharField(max_length=5, 
                                 choices=FileTypes.choices,
                                 default=FileTypes.NONE)
    upload_status = models.CharField(max_length=20,
                                     choices=UploadStatus.choices,
                                     default=UploadStatus.PENDING)

    def clean(self):
        super().clean()
        if self.file_type == self.FileTypes.NONE:
            raise IOError(f'File "{self.file_name}" has no file type')
        if self.file_type not in self.FileTypes.values:
            raise IOError(f'File type "{self.file_type}" is not valid')
        # Regular expression pattern to validate the path structure
        pattern = r'^[a-zA-Z0-9_/\\-]*$'
        if not re.match(pattern, self.file_path):
            raise IOError(f'File path is not valid\n\tfile path: {self.file_path}')

    def save(self, *args, **kwargs):
        if self.file_type == self.FileTypes.NONE and '.' in self.file_name:
            self.file_type = self.file_name.split('.')[-1]
        self.clean()
        super().save(*args, **kwargs)

class FileUploadFileHub(baseclass_models.MontrekHubABC):
    pass

class FileUploadFileStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(FileUploadFileHub, 
                                   on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
