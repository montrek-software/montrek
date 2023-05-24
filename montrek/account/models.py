from django.db import models
from django.db.models import Sum, F 
from typing import List
from baseclasses import models as baseclass_models
from .model_utils import get_transactions_by_account
# Create your models here.

class AccountHub(baseclass_models.MontrekHubABC): pass

class AccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    account_name = models.CharField(max_length=50) 
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)

class BankAccountSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    @property
    def account_value(self):
        transactions = get_transactions_by_account(self.hub_entity)
        return transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0

