from django.db import models

from baseclasses.models import MontrekTimeSeriesSatelliteABC
from showcase.models.stransaction_hub_models import STransactionHubValueDate


class STransactionSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(
        STransactionHubValueDate, on_delete=models.CASCADE
    )

    transaction_external_identifier = models.CharField(max_length=255)
    transaction_description = models.CharField(max_length=255)
    transaction_quantity = models.FloatField()
    transaction_price = models.FloatField()

    identifier_fields = ["value_date", "transaction_external_identifier"]
