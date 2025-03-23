from baseclasses import models as baseclass_models
from baseclasses.fields import HubForeignKey
from data_import.base.models.import_registry_base_models import (
    DataImportRegistryBaseSatelliteABC,
)
from django.db import models


class ApiRegistryHub(baseclass_models.MontrekHubABC):
    pass


class ApiRegistryHubValueDate(baseclass_models.HubValueDate):
    hub = HubForeignKey(ApiRegistryHub)


class ApiRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    hub_entity = models.ForeignKey(ApiRegistryHub, on_delete=models.CASCADE)
    import_url = models.URLField(default="", blank=True, null=True)
