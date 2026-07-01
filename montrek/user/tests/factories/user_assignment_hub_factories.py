import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
)
from user.models import UserAssignmentHub, UserAssignmentHubValueDate


class UserAssignmentHubFactory(MontrekHubFactory):
    class Meta:
        model = UserAssignmentHub


class UserAssignmentHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = UserAssignmentHubValueDate

    hub = factory.SubFactory(UserAssignmentHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
