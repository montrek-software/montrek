import factory
from baseclasses.utils import montrek_time


class TestMontrekHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestMontrekHub"


class TestMontrekSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestMontrekSatellite"

    hub_entity = factory.SubFactory(TestMontrekHubFactory)
    test_name = factory.Sequence(lambda n: f"Test Name {n}")
    state_date_start = montrek_time(2023, 6, 20)
    state_date_end = montrek_time(2023, 7, 10)

class TestLinkHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestLinkHub"
