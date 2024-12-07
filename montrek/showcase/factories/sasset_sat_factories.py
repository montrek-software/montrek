import factory

from showcase.factories.sasset_hub_factories import SAssetHubFactory
from showcase.models.sasset_sat_models import SAssetTypeSatellite, SAssetTypes


class SAssetTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SAssetTypeSatellite

    hub_entity = factory.SubFactory(SAssetHubFactory)
    asset_type = factory.Faker("random_element", elements=list(SAssetTypes))
