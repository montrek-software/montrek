from django.db import models

from baseclasses.models import MontrekTimeSeriesSatelliteABC
from showcase.models.transaction_hub_models import TransactionHubValueDate


class TransactionSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(
        TransactionHubValueDate, on_delete=models.CASCADE
    )

    transaction_external_identifier = models.CharField(max_length=255)
    transaction_description = models.CharField(max_length=255)
    transaction_quantity = models.FloatField()
    transaction_price = models.FloatField()
