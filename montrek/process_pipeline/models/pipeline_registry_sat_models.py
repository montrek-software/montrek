from django.db import models

from baseclasses.models import MontrekSatelliteABC


class PipelineRegistrySatelliteABC(MontrekSatelliteABC):
    class Meta:
        abstract = True

    celery_task_id = models.CharField(max_length=255, default="")
