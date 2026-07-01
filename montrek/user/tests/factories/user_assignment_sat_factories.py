import factory

from baseclasses.tests.factories.montrek_factory_schemas import MontrekSatelliteFactory
from user.models import UserAssignmentSatellite
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from user.tests.factories.user_assignment_hub_factories import UserAssignmentHubFactory


class UserAssignmentSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = UserAssignmentSatellite
        django_get_or_create = ("user",)

    hub_entity = factory.SubFactory(UserAssignmentHubFactory)
    user = factory.SubFactory(MontrekUserFactory)
