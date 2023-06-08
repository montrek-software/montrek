import factory
from account.tests.factories.account_factories import AccountHubFactory
from transaction.tests.factories.transaction_factories import TransactionHubFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionHubFactory

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

