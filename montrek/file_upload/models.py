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

    hub_entity = models.ForeignKey(FileUploadRegistryHub, 
                                   on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    file_type = models.CharField(max_length=5, 
                                 choices=FileTypes.choices,
                                 default=FileTypes.NONE)

    def clean(self):
        super().clean()
        if not self.file_name.endswith(f'.{self.file_type}'):
            raise ValidationError('File name does not match file type')
        # Regular expression pattern to validate the path structure
        pattern = r'^[a-zA-Z0-9_/\\-]*$'
        if not re.match(pattern, self.file_path):
            raise ValidationError('File path is not valid')

    def save(self, *args, **kwargs):
        if self.file_type == self.FileTypes.NONE and '.' in self.file_name:
            self.file_type = self.file_name.split('.')[-1]
        super().save(*args, **kwargs)
