import factory
from transaction.models import TransactionHub

class TransactionHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TransactionHub

class TransactionSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'transaction.TransactionSatellite'
    hub_entity = factory.SubFactory(TransactionHubFactory)
    transaction_date = factory.Faker('date_time')
    transaction_amount = factory.Faker('pyint')
    transaction_price = factory.Faker('pydecimal', left_digits=13, right_digits=2)
    transaction_description = factory.Faker('word')

class TransactionTypeHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'transaction.TransactionTypeHub'

class TransactionTypeSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'transaction.TransactionTypeSatellite'
    hub_entity = factory.SubFactory(TransactionTypeHubFactory)
    typename = 'INCOME'

class TransactionTransactionTypeLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'transaction.TransactionTransactionTypeLink'
    from_hub = factory.SubFactory(TransactionHubFactory)
    to_hub = factory.SubFactory(TransactionTypeHubFactory)
