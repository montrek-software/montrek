from django.db import models
from baseclasses import models as baseclass_models
from account import models as account_models

# Create your models here.
class TransactionHub(baseclass_models.MontrekHubABC): pass


class TransactionSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(account_models.AccountHub, on_delete=models.CASCADE)
    transaction_date = models.DateTimeField()
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50)
    transaction_description = models.CharField(max_length=50)
    transaction_category = models.CharField(max_length=50)
