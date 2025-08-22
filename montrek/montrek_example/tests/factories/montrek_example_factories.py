import factory
from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
    MontrekSatelliteFactory,
    MontrekTSSatelliteFactory,
)
from data_import.api_import.tests.factories.api_data_import_registry_factories import (
    ApiDataImportRegistryBaseSatelliteFactory,
)
from file_upload.tests.factories.field_map_factories import (
    FieldMapHubFactory,
    FieldMapStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryHubFactory,
    FileUploadRegistryStaticSatelliteFactory,
)


class HubAFactory(MontrekHubFactory):
    class Meta:
        model = "montrek_example.HubA"


class HubBFactory(MontrekHubFactory):
    class Meta:
        model = "montrek_example.HubB"


class HubCFactory(MontrekHubFactory):
    class Meta:
        model = "montrek_example.HubC"


class HubDFactory(MontrekHubFactory):
    class Meta:
        model = "montrek_example.HubD"


class AHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "montrek_example.AHubValueDate"

    hub = factory.SubFactory(HubAFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class BHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "montrek_example.BHubValueDate"

    hub = factory.SubFactory(HubBFactory)


class CHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "montrek_example.CHubValueDate"

    hub = factory.SubFactory(HubCFactory)


class DHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "montrek_example.DHubValueDate"

    hub = factory.SubFactory(HubDFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class SatA1Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatA1"

    hub_entity = factory.SubFactory(HubAFactory)


class SatA2Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatA2"

    hub_entity = factory.SubFactory(HubAFactory)


class SatA4Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatA4"

    hub_entity = factory.SubFactory(HubAFactory)


class SatA5Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatA5"

    hub_entity = factory.SubFactory(HubAFactory)


class SatB1Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatB1"

    hub_entity = factory.SubFactory(HubBFactory)


class SatB2Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatB2"

    hub_entity = factory.SubFactory(HubBFactory)


class SatC1Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatC1"

    hub_entity = factory.SubFactory(HubCFactory)


class SatTSC2Factory(MontrekTSSatelliteFactory):
    class Meta:
        model = "montrek_example.SatTSC2"

    hub_value_date = factory.SubFactory(CHubValueDateFactory)
    field_tsc2_float = factory.Faker("random_int", min=0, max=100)


class SatTSC3Factory(MontrekTSSatelliteFactory):
    class Meta:
        model = "montrek_example.SatTSC3"

    hub_value_date = factory.SubFactory(CHubValueDateFactory)
    field_tsc3_int = factory.Faker("random_int", min=0, max=100)
    field_tsc3_str = factory.Faker("word")


class SatD1Factory(MontrekSatelliteFactory):
    class Meta:
        model = "montrek_example.SatD1"

    hub_entity = factory.SubFactory(HubDFactory)


class SatTSD2Factory(MontrekTSSatelliteFactory):
    class Meta:
        model = "montrek_example.SatTSD2"

    hub_value_date = factory.SubFactory(DHubValueDateFactory)


class HubAFileUploadRegistryHubFactory(FileUploadRegistryHubFactory):
    class Meta:
        model = "montrek_example.HubAFileUploadRegistryHub"


class HubAFileUploadRegistryHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = "montrek_example.HubAFileUploadRegistryHubValueDate"

    hub = factory.SubFactory(HubAFileUploadRegistryHubFactory)


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


class HubAApiUploadRegistryHubFactory(MontrekHubFactory):
    class Meta:
        model = "montrek_example.HubAApiUploadRegistryHub"


class HubAApiUploadRegistryStaticSatelliteFactory(
    ApiDataImportRegistryBaseSatelliteFactory
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
