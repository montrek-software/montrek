import factory


class FieldMapHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FieldMapHub"


class FieldMapStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FieldMapStaticSatellite"

    hub_entity = factory.SubFactory(FieldMapHubFactory)
    source_field = factory.Sequence(lambda n: f"source_field_{n}")
    database_field = factory.Sequence(lambda n: f"database_field_{n}")
