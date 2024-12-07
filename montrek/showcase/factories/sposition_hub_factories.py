import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.models.sposition_hub_models import SPositionHub
from showcase.models.sposition_hub_models import SPositionHubValueDate


class SPositionHubFactory(MontrekHubFactory):
    class Meta:
        model = SPositionHub


class SPositionHubValueDate(MontrekHubValueDateFactory):
    class Meta:
        model = SPositionHubValueDate

    hub = factory.SubFactory(SPositionHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
