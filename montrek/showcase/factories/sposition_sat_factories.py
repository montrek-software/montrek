import factory

from showcase.factories.sposition_hub_factories import SPositionHubFactory
from showcase.models.sposition_sat_models import SPositionSatellite


class SPositionSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SPositionSatellite

    hub_entity = factory.SubFactory(SPositionHubFactory)
