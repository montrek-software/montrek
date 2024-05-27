from baseclasses.repositories.montrek_repository import MontrekRepository
from api_upload.models import (
    ApiUploadRegistryHub,
    ApiUploadRegistryStaticSatellite,
    ApiUploadRegistryHubABC,
    ApiUploadRegistryStaticSatelliteABC,
)


class ApiUploadRepositoryABC(MontrekRepository):
    hub_class = ApiUploadRegistryHubABC
    static_satellite_class = ApiUploadRegistryStaticSatelliteABC
    upload_status = ApiUploadRegistryStaticSatellite.UploadStatus

    def __init__(self, session_data={}):
        super().__init__(session_data=session_data)
        self._setup_checks()

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            self.static_satellite_class, ["url", "upload_status", "upload_message"]
        )
        return self.build_queryset()

    def _setup_checks(self):
        if self.hub_class is ApiUploadRegistryHubABC:
            raise NotImplementedError(
                "ApiUploadRepository class must have hub_class that is derived from ApiUploadRegistryHubABC"
            )
        if self.static_satellite_class is ApiUploadRegistryStaticSatelliteABC:
            raise NotImplementedError(
                "ApiUploadRepository class must have static_satellite_class that is derived from ApiUploadRegistryStaticSatelliteABC"
            )


class ApiUploadRepository(ApiUploadRepositoryABC):
    hub_class = ApiUploadRegistryHub
    static_satellite_class = ApiUploadRegistryStaticSatellite
