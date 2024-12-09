import factory

from showcase.factories.sasset_hub_factories import SAssetHubFactory
from showcase.models.sasset_sat_models import (
    SAssetStaticSatellite,
    SAssetTypeSatellite,
    SAssetTypes,
)


class SAssetTypeSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SAssetTypeSatellite

    hub_entity = factory.SubFactory(SAssetHubFactory)
    asset_type = factory.Faker("random_element", elements=list(SAssetTypes))


class SAssetStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SAssetStaticSatellite

    hub_entity = factory.SubFactory(SAssetHubFactory)
    asset_name = factory.Faker("word")

    @factory.post_generation
    def asset_type(self, create, extracted, **kwargs):
        if not create:
            return
        asset_type_kwargs = {"hub_entity": self.hub_entity}
        if extracted:
            asset_type_kwargs["asset_type"] = extracted
        SAssetTypeSatelliteFactory(**asset_type_kwargs)
