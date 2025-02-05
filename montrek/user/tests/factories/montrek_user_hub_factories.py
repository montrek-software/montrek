import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from user.models.montrek_user_hub_models import MontrekUserHub
from user.models.montrek_user_hub_models import MontrekUserHubValueDate


class MontrekUserHubFactory(MontrekHubFactory):
    class Meta:
        model = MontrekUserHub


class MontrekUserHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = MontrekUserHubValueDate

    hub = factory.SubFactory(MontrekUserHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
