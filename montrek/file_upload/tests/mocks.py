from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from file_upload.models import (
    FileUploadRegistryHub,
    FileUploadRegistryStaticSatellite,
    LinkFileUploadRegistryFileUploadFile,
)


class MockFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        LinkFileUploadRegistryFileUploadFile
    )


class MockWrongHubClassFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    pass


class MockWrongStaticSatelliteClassFileUploadRegistryRepository(
    FileUploadRegistryRepositoryABC
):
    hub_class = FileUploadRegistryHub


class MockWrongLinkFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite
