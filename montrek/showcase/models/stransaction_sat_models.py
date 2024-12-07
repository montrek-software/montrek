from django.db import models

from baseclasses.models import MontrekTimeSeriesSatelliteABC
from showcase.models.stransaction_hub_models import STransactionHubValueDate


class STransactionSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(
        STransactionHubValueDate, on_delete=models.CASCADE
    )

    stransaction_external_identifier = models.CharField(max_length=255)
    stransaction_description = models.CharField(max_length=255)
    stransaction_quantity = models.FloatField()
    stransaction_price = models.FloatField()
