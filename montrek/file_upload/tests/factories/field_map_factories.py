import factory

from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekSatelliteFactory,
)


class FieldMapHubFactory(MontrekHubFactory):
    class Meta:
        model = "file_upload.FieldMapHub"


class FieldMapStaticSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "file_upload.FieldMapStaticSatellite"

    hub_entity = factory.SubFactory(FieldMapHubFactory)
    source_field = factory.Sequence(lambda n: f"source_field_{n}")
    database_field = factory.Sequence(lambda n: f"database_field_{n}")
    function_name = "no_change"
