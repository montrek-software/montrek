from django.db import models

from baseclasses.models import MontrekSatelliteABC
from showcase.models.stransaction_hub_models import (
    STransactionHub,
)


class STransactionSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(STransactionHub, on_delete=models.CASCADE)

    transaction_date = models.DateField()
    transaction_external_identifier = models.CharField(max_length=255)
    transaction_description = models.CharField(max_length=255)
    transaction_quantity = models.FloatField()
    transaction_price = models.FloatField()

    identifier_fields = ["transaction_external_identifier"]
