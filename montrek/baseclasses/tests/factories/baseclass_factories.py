import factory

from baseclasses.utils import montrek_time
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
    MontrekSatelliteFactory,
    MontrekTSSatelliteFactory,
    ValueDateListFactory,
)


class TestMontrekHubFactory(MontrekHubFactory):
    class Meta:
        model = "baseclasses.TestMontrekHub"


class TestHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "baseclasses.TestHubValueDate"

    hub = factory.SubFactory(TestMontrekHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class TestMontrekSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "baseclasses.TestMontrekSatellite"

    hub_entity = factory.SubFactory(TestMontrekHubFactory)
    test_name = factory.Sequence(lambda n: f"Test Name {n}")
    test_date = montrek_time(2023, 6, 20)


class TestLinkHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestLinkHub"


class TestLinkSatelliteFactory(MontrekSatelliteFactory):
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


class TestMontrekSatelliteNoIdFieldsFactory(MontrekSatelliteFactory):
    class Meta:
        model = "baseclasses.TestMontrekSatelliteNoIdFields"

    hub_entity = factory.SubFactory(TestMontrekHubFactory)


class TestMontrekTimeSeriesSatelliteFactory(MontrekTSSatelliteFactory):
    class Meta:
        model = "baseclasses.TestMontrekTimeSeriesSatellite"

    hub_value_date = factory.SubFactory(TestHubValueDateFactory)
