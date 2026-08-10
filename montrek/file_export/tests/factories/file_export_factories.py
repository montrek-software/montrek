import factory
from django.core.files.base import ContentFile

from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekSatelliteFactory,
)

from file_export.models import FileExportRegistryStaticSatelliteABC

EXPORT_FILE_CONTENT = b"col1,col2\n1,2\n"
EXPORT_FILE_NAME = "test_export.csv"


class FileExportRegistryHubFactory(MontrekHubFactory):
    """Base factory for concrete FileExportRegistryHubABC subclasses.

    Subclasses only need to declare ``Meta.model``.
    """


class FileExportRegistryStaticSatelliteFactory(MontrekSatelliteFactory):
    """Base factory for concrete FileExportRegistryStaticSatelliteABC subclasses.

    Subclasses need to declare ``Meta.model`` and a ``hub_entity`` sub factory.
    """

    export_status = FileExportRegistryStaticSatelliteABC.ExportStatus.PROCESSED
    export_message = "Export successful"
    celery_task_id = ""

    @factory.post_generation
    def generate_export_file(self, create, extracted, **kwargs):
        """Pass ``generate_export_file=True`` to attach a small CSV export file."""
        if not create or not extracted:
            return
        self.export_file.save(
            EXPORT_FILE_NAME,
            ContentFile(EXPORT_FILE_CONTENT),
            save=True,
        )
