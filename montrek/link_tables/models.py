from django.db import models
from baseclasses.models import MontrekLinkABC
from account.models import AccountHub
from transaction.models import TransactionHub
from transaction.models import TransactionCategoryMapHub
from credit_institution.models import CreditInstitutionHub
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadFileHub

# Create your models here.
class AccountTransactionLink(MontrekLinkABC):
    from_hub = models.ForeignKey(AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_transaction_link_from_hub')
    to_hub = models.ForeignKey(TransactionHub, 
                               on_delete=models.CASCADE, 
                               related_name='account_transaction_to_hub')

class AccountCreditInstitutionLink(MontrekLinkABC):
    from_hub = models.ForeignKey(AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_credit_institution_link_from_hub')
    to_hub = models.ForeignKey(CreditInstitutionHub, 
                               on_delete=models.CASCADE, 
                               related_name='account_credit_institution_link_to_hub')

class FileUploadRegistryTransactionLink(MontrekLinkABC):
    from_hub = models.ForeignKey(FileUploadRegistryHub,
                                 on_delete=models.CASCADE,
                                 related_name='file_upload_registry_transaction_link_from_hub')
    to_hub = models.ForeignKey(TransactionHub, 
                               on_delete=models.CASCADE, 
                               related_name='file_upload_registry_transaction_link_to_hub')

class AccountFileUploadRegistryLink(MontrekLinkABC):
    from_hub = models.ForeignKey(AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_file_upload_registry_link_from_hub')
    to_hub = models.ForeignKey(FileUploadRegistryHub, 
                               on_delete=models.CASCADE, 
                               related_name='account_file_upload_registry_link_to_hub')
class FileUploadRegistryFileUploadFileLink(MontrekLinkABC):
    from_hub = models.ForeignKey(FileUploadRegistryHub,
                                 on_delete=models.CASCADE,
                                 related_name='file_upload_registry_file_upload_file_link_from_hub')
    to_hub = models.ForeignKey(FileUploadFileHub, 
                               on_delete=models.CASCADE, 
                               related_name='file_upload_registry_file_upload_file_link_to_hub')

class AccountTransactionCategoryMapLink(MontrekLinkABC):
    from_hub = models.ForeignKey(AccountHub,
                                 on_delete=models.CASCADE,
                                 related_name='account_transaction_category_map_link_from_hub')
    to_hub = models.ForeignKey(TransactionCategoryMapHub,
                               on_delete=models.CASCADE,
                               related_name='account_transaction_category_map_link_to_hub')
