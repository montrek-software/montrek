import factory

from showcase.factories.product_hub_factories import ProductHubFactory
from showcase.models.product_sat_models import ProductSatellite


class ProductSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductSatellite

    hub_entity = factory.SubFactory(ProductHubFactory)
    product_name = factory.Faker("word")
    inception_date = factory.Faker("date")
