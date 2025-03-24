from data_import.base.models.import_registry_base_models import (
    DataImportRegistryBaseSatelliteABC,
)
from django.db import models
from baseclasses.fields import HubForeignKey

from baseclasses.models import HubValueDate, MontrekHubABC




class ApiRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    class Meta:
        abstract = True
    import_url = models.URLField(default="", blank=True, null=True)

class MockApiRegistryHub(MontrekHubABC):
    pass

class MockApiRegistryHubValueDate(HubValueDate):
    hub = HubForeignKey(MockApiRegistryHub)
    
class MockApiRegistrySatellite(ApiRegistrySatellite):
    hub_entity = models.ForeignKey(MockApiRegistryHub, on_delete=models.CASCADE)
