import factory
from account.tests.factories.account_factories import AccountHubFactory
from transaction.tests.factories.transaction_factories import TransactionHubFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionHubFactory
from file_upload.tests.factories.file_upload_factories import FileUploadRegistryHubFactory
from file_upload.tests.factories.file_upload_factories import FileUploadFileHubFactory


class AccountTransactionLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'link_tables.AccountTransactionLink'
    from_hub = factory.SubFactory(AccountHubFactory)
    to_hub = factory.SubFactory(TransactionHubFactory)

class AccountCreditInstitutionLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'link_tables.AccountCreditInstitutionLink'
    from_hub = factory.SubFactory(AccountHubFactory)
    to_hub = factory.SubFactory(CreditInstitutionHubFactory)

class AccountFileUploadRegistryLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'link_tables.AccountFileUploadRegistryLink'
    from_hub = factory.SubFactory(AccountHubFactory)
    to_hub = factory.SubFactory(FileUploadRegistryHubFactory)

class FileUploadRegistryFileUploadFileLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'link_tables.FileUploadRegistryFileUploadFileLink'
    from_hub = factory.SubFactory(FileUploadRegistryHubFactory)
    to_hub = factory.SubFactory(FileUploadFileHubFactory)

class AccountTransactionCategoryMapLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'link_tables.AccountTransactionCategoryMapLink'
    from_hub = factory.SubFactory(AccountHubFactory)
    to_hub = factory.SubFactory(TransactionHubFactory)
