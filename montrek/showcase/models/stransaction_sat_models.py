from django.db import models

from baseclasses.models import MontrekSatelliteABC
from file_upload.models import FileUploadRegistryStaticSatelliteABC
from showcase.models.stransaction_hub_models import (
    STransactionFURegistryHub,
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


class STransactionFURegistryStaticSatellite(FileUploadRegistryStaticSatelliteABC):
    hub_entity = models.ForeignKey(STransactionFURegistryHub, on_delete=models.CASCADE)
