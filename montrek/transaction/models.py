from django.db import models
from baseclasses import models as baseclass_models
from account import models as account_models

# Create your models here.
class TransactionHub(baseclass_models.MontrekHubABC): pass


class TransactionSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TransactionHub,
                                   on_delete=models.CASCADE)
    identifier_fields = ['transaction_date',
                         'transaction_type',
                         'transaction_party',
                         'transaction_category']
    transaction_date = models.DateTimeField()
    transaction_amount = models.IntegerField()
    transaction_price = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=50)
    transaction_description = models.TextField()
    transaction_category = models.CharField(max_length=50)
    transaction_party = models.CharField(max_length=50, default='NONE')

    @property
    def transaction_value(self):
        return self.transaction_amount * self.transaction_price
