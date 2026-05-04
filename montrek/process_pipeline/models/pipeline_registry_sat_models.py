from django.db import models

from baseclasses.models import MontrekSatelliteABC
from process_pipeline.models.pipeline_registry_hub_models import PipelineRegistryHubABC


class PipelineRegistrySatelliteABC(MontrekSatelliteABC):
    class Meta:
        abstract = True

    hub_entity = models.ForeignKey(PipelineRegistryHubABC, on_delete=models.CASCADE)
    celery_task_id = models.CharField(max_length=255, default="")
