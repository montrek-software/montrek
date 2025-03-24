from data_import.base.models.import_registry_base_models import (
    DataImportRegistryBaseSatelliteABC,
)
from django.db import models




class ApiRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    class Meta:
        abstract = True
    import_url = models.URLField(default="", blank=True, null=True)
