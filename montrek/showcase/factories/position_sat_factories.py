import factory

from showcase.factories.position_hub_factories import PositionHubFactory
from showcase.models.position_sat_models import PositionSatellite


class PositionSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PositionSatellite

    hub_entity = factory.SubFactory(PositionHubFactory)
