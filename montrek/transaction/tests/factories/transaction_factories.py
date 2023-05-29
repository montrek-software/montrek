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
    transaction_type = factory.Faker('word')
    transaction_description = factory.Faker('word')
    transaction_category = factory.Faker('word')
