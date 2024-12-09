import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.factories.sasset_hub_factories import SAssetHubFactory
from showcase.factories.sproduct_hub_factories import SProductHubFactory
from showcase.models.stransaction_hub_models import STransactionHub
from showcase.models.stransaction_hub_models import STransactionHubValueDate


class STransactionHubFactory(MontrekHubFactory):
    class Meta:
        model = STransactionHub


class STransactionHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = STransactionHubValueDate

    hub = factory.SubFactory(STransactionHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class LinkSTransactionSProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "showcase.LinkSTransactionSProduct"

    hub_in = factory.SubFactory(STransactionHubFactory)
    hub_out = factory.SubFactory(SProductHubFactory)


class LinkSTransactionSAssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "showcase.LinkSTransactionSAsset"

    hub_in = factory.SubFactory(STransactionHubFactory)
    hub_out = factory.SubFactory(SAssetHubFactory)
