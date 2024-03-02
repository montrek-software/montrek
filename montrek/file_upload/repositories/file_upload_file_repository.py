from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadFileHub
from file_upload.models import FileUploadFileStaticSatellite


class FileUploadFileRepository(MontrekRepository):
    hub_class = FileUploadFileHub

    def std_queryset(self, **kwargs):
        self.add_satellite_fields_annotations(
            FileUploadFileStaticSatellite,
            ["file"],
        )
        queryset = self.build_queryset()
        return queryset
