import factory

from showcase.factories.sproduct_hub_factories import SProductHubFactory
from showcase.models.sproduct_sat_models import SProductSatellite


class SProductSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SProductSatellite

    hub_entity = factory.SubFactory(SProductHubFactory)
    product_name = factory.Faker("word")
    inception_date = factory.Faker("date")
