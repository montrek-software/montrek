import factory

class AssetHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetHub"

class AssetStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetStaticSatellite"
    hub_entity = factory.SubFactory(AssetHubFactory)
    name = factory.Sequence(lambda n: f"AssetStaticSatellite {n}")

class AssetTimeSeriesSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset.AssetTimeSeriesSatellite"
    hub_entity = factory.SubFactory(AssetHubFactory)
