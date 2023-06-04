import re
from django.db import models
from django.db.models import Sum, F 
from typing import List
from baseclasses import models as baseclass_models
from .model_utils import get_transactions_by_account
# Create your models here.

class AccountHub(baseclass_models.MontrekHubABC): pass

class AccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    class AccountType(models.TextChoices):
        BANKACCOUNT = "BankAccount"
        CASH = "Cash"
        DEPOT = "Depot"
        REAL_ESTATE = "RealEstate"
        OTHER = "Other"

    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=50, choices=AccountType.choices, default=AccountType.OTHER)
    account_name = models.CharField(max_length=50) 
    @property
    def view_name(self):
        if self.account_type == self.AccountType.OTHER:
            return 'account_view'
        else:
            view_rep = re.sub(r'(?<!^)(?=[A-Z])', '_',
                              self.account_type).lower()
            return f'{view_rep}_view'

class BankAccountPropertySatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    @property
    def account_value(self):
        transactions = get_transactions_by_account(self.hub_entity)
        return transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0

class BankAccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
