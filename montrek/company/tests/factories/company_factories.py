import factory


class CompanyHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "company.CompanyHub"


class CompanyStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "company.CompanyStaticSatellite"

    hub_entity = factory.SubFactory(CompanyHubFactory)
    company_name = factory.Sequence(lambda n: f"company_name_{n}")
    bloomberg_ticker = factory.Sequence(lambda n: f"bloomberg_ticker_{n}")
    effectual_company_id = factory.Sequence(lambda n: f"effectual_company_id_{n}")


class CompanyTimeSeriesSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "company.CompanyTimeSeriesSatellite"

    hub_entity = factory.SubFactory(CompanyHubFactory)
