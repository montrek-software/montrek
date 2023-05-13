from django.db import models
from baseclasses import models as baseclass_models
from account import models as account_models
from transaction import models as transaction_models

# Create your models here.
class AccountTransactionLink(baseclass_models.MontrekLinkABC):
    from_hub = models.ForeignKey(account_models.AccountHub, on_delete=models.CASCADE, related_name='from_hub')
    to_hub = models.ForeignKey(transaction_models.TransactionHub, on_delete=models.CASCADE, related_name='to_hub')
