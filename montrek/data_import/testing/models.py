from baseclasses import models as baseclass_models
from baseclasses.fields import HubForeignKey
from data_import.base.models import DataImportRegistryBaseSatelliteABC
from django.db import models
from process_pipeline.models.pipeline_registry_hub_models import PipelineRegistryHubABC


class TestRegistryHub(PipelineRegistryHubABC): ...


class TestRegistryHubValueDate(baseclass_models.HubValueDate):
    hub = HubForeignKey(TestRegistryHub)


class TestRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    hub_entity = models.ForeignKey(TestRegistryHub, on_delete=models.CASCADE)


class TestApiRegistrySatellite(DataImportRegistryBaseSatelliteABC):
    hub_entity = models.ForeignKey(TestRegistryHub, on_delete=models.CASCADE)
    import_url = models.URLField(default="", blank=True, null=True)
