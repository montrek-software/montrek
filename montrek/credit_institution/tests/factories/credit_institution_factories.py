import factory


class CreditInstitutionHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "credit_institution.CreditInstitutionHub"


class CreditInstitutionStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "credit_institution.CreditInstitutionStaticSatellite"

    hub_entity = factory.SubFactory(CreditInstitutionHubFactory)
    credit_institution_name = factory.Faker("company")
