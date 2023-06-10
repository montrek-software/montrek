from django.db import models

from baseclasses import models as baseclass_models
# Create your models here.

class FileUploadRegistryHub(baseclass_models.MontrekHubABC):
    pass

class FileUploadRegistryStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(FileUploadRegistryHub, on_delete=models.CASCADE)
