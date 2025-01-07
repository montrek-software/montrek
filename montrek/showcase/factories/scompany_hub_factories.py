import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from mt_economic_common.country.tests.factories.country_factories import (
    CountryHubFactory,
)
from showcase.models.scompany_hub_models import LinkSCompanyCountry, SCompanyHub
from showcase.models.scompany_hub_models import SCompanyHubValueDate


class SCompanyHubFactory(MontrekHubFactory):
    class Meta:
        model = SCompanyHub


class SCompanyHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SCompanyHubValueDate

    hub = factory.SubFactory(SCompanyHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class LinkSCompanyCountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LinkSCompanyCountry

    hub_in = factory.SubFactory(SCompanyHubFactory)
    hub_out = factory.SubFactory(CountryHubFactory)
