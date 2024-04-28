from baseclasses.repositories.montrek_repository import MontrekRepository
from api_upload.models import (
    ApiUploadRegistryHub,
    ApiUploadRegistryStaticSatellite,
)


class ApiUploadRepository(MontrekRepository):
    hub_class = ApiUploadRegistryHub

    upload_status = ApiUploadRegistryStaticSatellite.UploadStatus

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            ApiUploadRegistryStaticSatellite, ["url", "upload_status", "upload_message"]
        )
        return self.build_queryset()
