import factory

from showcase.models.product_hub_models import ProductHub


class ProductHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductHub
