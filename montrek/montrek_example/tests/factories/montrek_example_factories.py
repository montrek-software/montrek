import factory
from django.utils import timezone


class HubAFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.HubA"


class HubBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.HubB"


class HubCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.HubC"


class HubDFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.HubD"


class SatA1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatA1"

    hub_entity = factory.SubFactory(HubAFactory)


class SatA2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatA2"

    hub_entity = factory.SubFactory(HubAFactory)


class SatB1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatB1"

    hub_entity = factory.SubFactory(HubBFactory)


class SatB2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatB2"

    hub_entity = factory.SubFactory(HubBFactory)


class SatC1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatC1"

    hub_entity = factory.SubFactory(HubCFactory)


class SatTSC2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatTSC2"

    hub_entity = factory.SubFactory(HubCFactory)
    value_date = factory.Faker("date_time", tzinfo=timezone.utc)


class SatD1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatD1"

    hub_entity = factory.SubFactory(HubDFactory)


class LinkHubAHubBFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubAHubB"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(HubBFactory)


class LinkHubAHubCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubAHubC"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(HubCFactory)


class LinkHubBHubDFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubBHubD"

    hub_in = factory.SubFactory(HubBFactory)
    hub_out = factory.SubFactory(HubDFactory)
