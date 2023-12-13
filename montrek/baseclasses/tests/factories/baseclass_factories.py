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

    in_hub = factory.SubFactory(TestMontrekHubFactory)
    out_hub = factory.SubFactory(TestLinkHubFactory)


class HubAFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.HubA"


class HubBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.HubB"


class HubCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.HubC"


class SatA1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatA1"

    hub_entity = factory.SubFactory(HubAFactory)


class SatA2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatA2"

    hub_entity = factory.SubFactory(HubAFactory)


class SatB1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatB1"

    hub_entity = factory.SubFactory(HubBFactory)


class SatB2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatB2"

    hub_entity = factory.SubFactory(HubBFactory)

class SatC1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatC1"

    hub_entity = factory.SubFactory(HubCFactory)

class SatTSC2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.SatTSC2"
    hub_entity=factory.SubFactory(HubCFactory)

class LinkHubAHubBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.LinkHubAHubB"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(HubBFactory)

class LinkHubAHubCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.LinkHubAHubC"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(HubCFactory)
        

