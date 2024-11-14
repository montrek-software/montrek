import os
from django.contrib import messages
from django.core.files import File
from django.conf import settings
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadRegistryHubABC
from file_upload.models import FileUploadRegistryStaticSatelliteABC
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import (
    FileUploadRegistryHub,
    FileUploadRegistryStaticSatellite,
    LinkFileUploadRegistryFileUploadFile,
    LinkFileUploadRegistryFileLogFile,
)


class NotImplementedLinkFileUploadRegistryFile:
    pass


class FileUploadRegistryRepositoryABC(MontrekRepository):
    hub_class = FileUploadRegistryHubABC
    static_satellite_class = FileUploadRegistryStaticSatelliteABC
    link_file_upload_registry_file_upload_file_class = (
        NotImplementedLinkFileUploadRegistryFile
    )
    link_file_upload_registry_file_log_file_class = (
        NotImplementedLinkFileUploadRegistryFile
    )
    default_order_fields = ("-upload_date",)

    def __init__(self, session_data={}):
        self._setup_checks()
        super().__init__(session_data=session_data)

    def set_annotations(self, **kwargs):
        self.add_satellite_fields_annotations(
            self.static_satellite_class,
            ["file_name", "file_type", "upload_status", "upload_message"],
        )
        if (
            self.link_file_upload_registry_file_log_file_class
            is not NotImplementedLinkFileUploadRegistryFile
        ):
            self.add_linked_satellites_field_annotations(
                FileUploadFileStaticSatellite,
                self.link_file_upload_registry_file_log_file_class,
                ["file"],
            )
            self.rename_field("file", "log_file")
        self.add_linked_satellites_field_annotations(
            FileUploadFileStaticSatellite,
            self.link_file_upload_registry_file_upload_file_class,
            ["file"],
        )
        self.rename_field("created_at", "upload_date")

    def _setup_checks(self):
        if self.hub_class is FileUploadRegistryHubABC:
            raise NotImplementedError(
                "FileUploadRegistryRepository class must have hub_class that is derived from FileUploadRegistryHubABC"
            )
        if self.static_satellite_class is FileUploadRegistryStaticSatelliteABC:
            raise NotImplementedError(
                "FileUploadRegistryRepository class must have static_satellite_class that is derived from FileUploadRegistryStaticSatelliteABC"
            )
        if (
            self.link_file_upload_registry_file_upload_file_class
            is NotImplementedLinkFileUploadRegistryFile
        ):
            raise NotImplementedError(
                "FileUploadRegistryRepository class must have link_file_upload_registry_file_upload_file that is not NotImplementedLinkFileUploadRegistryFileUploadFile"
            )

    def get_upload_file_from_registry(
        self, file_upload_registry_id: int, request
    ) -> File | None:
        file_upload_registry_path = (
            self.receive().get(hub__pk=file_upload_registry_id).file
        )
        return self._get_file_from_registry(file_upload_registry_path, request)

    def get_log_file_from_registry(
        self, file_log_registry_id: int, request
    ) -> File | None:
        file_log_registry_path = (
            self.receive().get(hub__pk=file_log_registry_id).log_file
        )

        return self._get_file_from_registry(file_log_registry_path, request)

    def _get_file_from_registry(
        self, file_registry_path: str | None, request
    ) -> File | None:
        if not file_registry_path:
            return None
        file_registry_path = os.path.join(settings.MEDIA_ROOT, file_registry_path)
        if not os.path.exists(file_registry_path):
            messages.error(request, f"File {file_registry_path} not found")
            return None
        return open(file_registry_path, "rb")


class FileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        LinkFileUploadRegistryFileUploadFile
    )
    link_file_upload_registry_file_log_file_class = LinkFileUploadRegistryFileLogFile
