import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.models.scompany_hub_models import SCompanyHub
from showcase.models.scompany_hub_models import SCompanyHubValueDate


class SCompanyHubFactory(MontrekHubFactory):
    class Meta:
        model = SCompanyHub


class SCompanyHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SCompanyHubValueDate

    hub = factory.SubFactory(SCompanyHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
