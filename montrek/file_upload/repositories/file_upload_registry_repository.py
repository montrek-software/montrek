from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import LinkFileUploadRegistryFileUploadFile

class FileUploadRegistryRepository(MontrekRepository):
    hub_class=FileUploadRegistryHub
    def std_queryset(self, **kwargs):
        reference_date=timezone.now()
        self.add_satellite_fields_annotations(
            FileUploadRegistryStaticSatellite,
            ['file_name', 'file_type', 'upload_status', 'upload_message'],
            reference_date=reference_date,
        )
        self.add_linked_satellites_field_annotations(
            FileUploadFileStaticSatellite,
            LinkFileUploadRegistryFileUploadFile,
            ['file'],
            reference_date=reference_date,
        )
        queryset = self.build_queryset()
        return queryset
