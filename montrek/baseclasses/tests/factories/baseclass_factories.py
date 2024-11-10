import datetime

import factory

from baseclasses.utils import montrek_time


class TestMontrekHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestMontrekHub"


class ValueDateListFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.ValueDateList"

    value_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)


class TestHubValueDateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestHubValueDate"

    hub = factory.SubFactory(TestMontrekHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class TestMontrekSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.TestMontrekSatellite"

    hub_entity = factory.SubFactory(TestMontrekHubFactory)
    test_name = factory.Sequence(lambda n: f"Test Name {n}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        TestHubValueDateFactory(hub=instance.hub_entity)
        return instance


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
