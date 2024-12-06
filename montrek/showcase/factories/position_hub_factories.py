import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from showcase.models.position_hub_models import PositionHub
from showcase.models.position_hub_models import PositionHubValueDate


class PositionHubFactory(MontrekHubFactory):
    class Meta:
        model = PositionHub


class PositionHubValueDate(MontrekHubValueDateFactory):
    class Meta:
        model = PositionHubValueDate

    hub = factory.SubFactory(PositionHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
