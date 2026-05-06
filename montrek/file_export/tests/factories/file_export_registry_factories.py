import factory
from django.core.files.base import ContentFile

from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekSatelliteFactory,
)


class TestFileExportRegistryHubFactory(MontrekHubFactory):
    class Meta:
        model = "file_export.TestFileExportRegistryHub"


class TestFileExportRegistryStaticSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "file_export.TestFileExportRegistryStaticSatellite"

    hub_entity = factory.SubFactory(TestFileExportRegistryHubFactory)
    export_status = "pending"
    export_message = ""
    celery_task_id = ""

    @factory.post_generation
    def generate_export_file(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.export_file.save(
            "test_export.csv",
            ContentFile(b"col1,col2\n1,2\n"),
            save=True,
        )
