import factory


class CountryHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "country.CountryHub"


class CountryStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "country.CountryStaticSatellite"

    hub_entity = factory.SubFactory(CountryHubFactory)
    country_name = factory.Sequence(lambda n: f"country_name_{n}")
    country_code = factory.Sequence(lambda n: f"{n:03d}")
