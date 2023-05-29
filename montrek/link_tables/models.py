from django.db import models
from baseclasses import models as baseclass_models
from account import models as account_models
from transaction import models as transaction_models
from credit_institution import models as credit_institution_models

# Create your models here.
class AccountTransactionLink(baseclass_models.MontrekLinkABC):
    from_hub = models.ForeignKey(account_models.AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_transaction_link_from_hub')
    to_hub = models.ForeignKey(transaction_models.TransactionHub, 
                               on_delete=models.CASCADE, 
                               related_name='account_transaction_to_hub')

class AccountCreditInstituteLink(baseclass_models.MontrekLinkABC):
    from_hub = models.ForeignKey(account_models.AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_credit_institute_link_from_hub')
    to_hub = models.ForeignKey(credit_institution_models.CreditInstitutionHub, 
                               on_delete=models.CASCADE, 
                               related_name='account_credit_institute_link_to_hub')
