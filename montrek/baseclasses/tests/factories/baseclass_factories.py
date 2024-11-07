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


class TestLinkHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestLinkHub"


class TestLinkSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestLinkSatellite"

    hub_entity = factory.SubFactory(TestLinkHubFactory)
    test_id = factory.Sequence(lambda n: n)
    state_date_start = montrek_time(2023, 6, 20)
    state_date_end = montrek_time(2023, 7, 10)


class LinkTestMontrekTestLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.LinkTestMontrekTestLink"

    hub_in = factory.SubFactory(TestMontrekHubFactory)
    hub_out = factory.SubFactory(TestLinkHubFactory)


class TestMontrekSatelliteNoIdFieldsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestMontrekSatelliteNoIdFields"

    hub_entity = factory.SubFactory(TestMontrekHubFactory)
