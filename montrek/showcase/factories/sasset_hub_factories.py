import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.factories.scompany_hub_factories import SCompanyHubFactory
from showcase.models.sasset_hub_models import LinkSAssetSCompany, SAssetHub
from showcase.models.sasset_hub_models import SAssetHubValueDate


class SAssetHubFactory(MontrekHubFactory):
    class Meta:
        model = SAssetHub


class SAssetHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SAssetHubValueDate

    hub = factory.SubFactory(SAssetHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class LinkSAssetSCompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LinkSAssetSCompany

    hub_in = factory.SubFactory(SAssetHubFactory)
    hub_out = factory.SubFactory(SCompanyHubFactory)
