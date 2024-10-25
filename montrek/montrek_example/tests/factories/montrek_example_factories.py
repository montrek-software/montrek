import factory
import datetime

from api_upload.tests.factories import (
    ApiUploadRegistryHubFactory,
    ApiUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryHubFactory,
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.field_map_factories import (
    FieldMapHubFactory,
    FieldMapStaticSatelliteFactory,
)


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
    value_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    field_tsc2_float = factory.Faker("random_int", min=0, max=100)


class SatTSC3Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatTSC3"

    hub_entity = factory.SubFactory(HubCFactory)
    value_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    field_tsc3_int = factory.Faker("random_int", min=0, max=100)
    field_tsc3_str = factory.Faker("word")


class SatD1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatD1"

    hub_entity = factory.SubFactory(HubDFactory)


class SatTSD2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.SatTSD2"

    hub_entity = factory.SubFactory(HubDFactory)
    value_date = factory.Faker("date_time", tzinfo=datetime.timezone.utc)


class HubAFileUploadRegistryHubFactory(FileUploadRegistryHubFactory):
    class Meta:
        model = "montrek_example.HubAFileUploadRegistryHub"


class HubAFileUploadRegistryStaticSatelliteFactory(
    FileUploadRegistryStaticSatelliteFactory
):
    class Meta:
        model = "montrek_example.HubAFileUploadRegistryStaticSatellite"

    hub_entity = factory.SubFactory(HubAFileUploadRegistryHubFactory)


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


class LinkHubCHubDFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubCHubD"

    hub_in = factory.SubFactory(HubCFactory)
    hub_out = factory.SubFactory(HubDFactory)


class HubAApiUploadRegistryHubFactory(ApiUploadRegistryHubFactory):
    class Meta:
        model = "montrek_example.HubAApiUploadRegistryHub"


class HubAApiUploadRegistryStaticSatelliteFactory(
    ApiUploadRegistryStaticSatelliteFactory
):
    class Meta:
        model = "montrek_example.HubAApiUploadRegistryStaticSatellite"

    hub_entity = factory.SubFactory(HubAApiUploadRegistryHubFactory)


class LinkHubAApiUploadRegistryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubAApiUploadRegistry"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(HubAApiUploadRegistryHubFactory)


class LinkHubAFileUploadRegistryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "montrek_example.LinkHubAFileUploadRegistry"

    hub_in = factory.SubFactory(HubAFactory)
    hub_out = factory.SubFactory(FileUploadRegistryHubFactory)


class SatA1FieldMapHubFactory(FieldMapHubFactory):
    class Meta:
        model = "montrek_example.SatA1FieldMapHub"


class SatA1FieldMapStaticSatelliteFactory(FieldMapStaticSatelliteFactory):
    class Meta:
        model = "montrek_example.SatA1FieldMapStaticSatellite"

    hub_entity = factory.SubFactory(SatA1FieldMapHubFactory)
