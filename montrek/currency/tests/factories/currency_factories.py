import factory

class CurrencyHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "currency.CurrencyHub"

class CurrencyStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "currency.CurrencyStaticSatellite"
    hub_entity = factory.SubFactory(CurrencyHubFactory)

class CurrencyTimeSeriesSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "currency.CurrencyTimeSeriesSatellite"
    hub_entity = factory.SubFactory(CurrencyHubFactory)
