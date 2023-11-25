import factory
from currency.tests.factories.currency_factories import CurrencyHubFactory

class AssetHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetHub"

class AssetStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetStaticSatellite"
    hub_entity = factory.SubFactory(AssetHubFactory)
    asset_name = factory.Sequence(lambda n: f"AssetStaticSatellite {n}")

class AssetLiquidSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetLiquidSatellite"
    hub_entity = factory.SubFactory(AssetHubFactory)

class AssetTimeSeriesSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetTimeSeriesSatellite"
    hub_entity = factory.SubFactory(AssetHubFactory)
