from django.db import models

from baseclasses.models import MontrekTimeSeriesSatelliteABC
from showcase.models.position_hub_models import PositionHubValueDate


class PositionSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(PositionHubValueDate, on_delete=models.CASCADE)
