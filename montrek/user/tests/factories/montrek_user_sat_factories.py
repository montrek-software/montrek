import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)

from user.tests.factories.montrek_user_hub_factories import MontrekUserHubFactory
from user.models.montrek_user_sat_models import MontrekUserSatellite


class MontrekUserSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = MontrekUserSatellite

    hub_entity = factory.SubFactory(MontrekUserHubFactory)
