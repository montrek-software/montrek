import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.factories.product_hub_factories import ProductHubFactory
from showcase.models.transaction_hub_models import TransactionHub
from showcase.models.transaction_hub_models import TransactionHubValueDate


class TransactionHubFactory(MontrekHubFactory):
    class Meta:
        model = TransactionHub


class TransactionHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = TransactionHubValueDate

    hub = factory.SubFactory(TransactionHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class LinkTransactionProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "showcase.LinkTransactionProduct"

    hub_in = factory.SubFactory(TransactionHubFactory)
    hub_out = factory.SubFactory(ProductHubFactory)
