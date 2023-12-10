import factory
from django.utils import timezone
from transaction.models import TransactionHub
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


class TransactionHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TransactionHub

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of AccountHub instances were passed in, link them
            for account in extracted:
                self.link_transaction_account.add(account)
        else:
            # Link a default AccountHub for this TransactionCategoryMapHub
            account = AccountStaticSatelliteFactory.create()
            self.link_transaction_account.add(account.hub_entity)


class TransactionSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionSatellite"

    hub_entity = factory.SubFactory(TransactionHubFactory)
    transaction_date = factory.Faker("date_time", tzinfo=timezone.utc)
    transaction_amount = factory.Faker("pyint")
    transaction_price = factory.Faker("pydecimal", left_digits=13, right_digits=2)
    transaction_description = factory.Faker("word")


class TransactionTypeHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionTypeHub"


class TransactionTypeSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionTypeSatellite"

    hub_entity = factory.SubFactory(TransactionTypeHubFactory)
    typename = "INCOME"


class TransactionCategoryHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionCategoryHub"


class TransactionCategorySatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionCategorySatellite"

    hub_entity = factory.SubFactory(TransactionCategoryHubFactory)
    typename = "EXAMPLE"


class TransactionCategoryMapHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionCategoryMapHub"

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of AccountHub instances were passed in, link them
            for account in extracted:
                self.link_transaction_category_map_account.add(account)
        else:
            # Link a default AccountHub for this TransactionCategoryMapHub
            account = AccountStaticSatelliteFactory.create()
            self.link_transaction_category_map_account.add(account.hub_entity)


class TransactionCategoryMapSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "transaction.TransactionCategoryMapSatellite"

    hub_entity = factory.SubFactory(TransactionCategoryMapHubFactory)
