import factory

from showcase.factories.scompany_hub_factories import SCompanyHubFactory
from showcase.models.scompany_sat_models import SCompanyStaticSatellite


class SCompanyStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SCompanyStaticSatellite

    hub_entity = factory.SubFactory(SCompanyHubFactory)
