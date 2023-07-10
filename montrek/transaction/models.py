from django.db import models
from baseclasses import models as baseclass_models
from account import models as account_models
from account.managers.validators import montrek_iban_validator

# Create your models here.
class TransactionHub(baseclass_models.MontrekHubABC): pass


class TransactionSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TransactionHub,
                                   on_delete=models.CASCADE)
    identifier_fields = ['transaction_date',
                         'transaction_type',
                         'transaction_party',
                         'transaction_party_iban',
                         'transaction_category',
                        ]
    transaction_date = models.DateTimeField()
    transaction_amount = models.IntegerField()
    transaction_price = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=50)
    transaction_description = models.TextField()
    transaction_category = models.CharField(max_length=50)
    transaction_party = models.CharField(max_length=250, default='NONE')
    transaction_party_iban = models.CharField(
        max_length=34,
        validators=[montrek_iban_validator()],
        default='XX00000000000000000000'
    )

    @property
    def transaction_value(self):
        return self.transaction_amount * self.transaction_price
