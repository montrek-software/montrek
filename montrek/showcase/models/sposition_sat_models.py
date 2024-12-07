from django.db import models

from baseclasses.models import MontrekTimeSeriesSatelliteABC
from showcase.models.sposition_hub_models import SPositionHubValueDate


class SPositionSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(SPositionHubValueDate, on_delete=models.CASCADE)
