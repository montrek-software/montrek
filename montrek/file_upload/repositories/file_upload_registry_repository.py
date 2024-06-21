import os
from typing import TextIO
from django.contrib import messages
from montrek.settings import MEDIA_ROOT
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadRegistryHubABC
from file_upload.models import FileUploadRegistryStaticSatelliteABC
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import (
    FileUploadRegistryHub,
    FileUploadRegistryStaticSatellite,
    LinkFileUploadRegistryFileUploadFile,
)


class NotImplementedLinkFileUploadRegistryFileUploadFile:
    pass


class FileUploadRegistryRepositoryABC(MontrekRepository):
    hub_class = FileUploadRegistryHubABC
    static_satellite_class = FileUploadRegistryStaticSatelliteABC
    link_file_upload_registry_file_upload_file_class = (
        NotImplementedLinkFileUploadRegistryFileUploadFile
    )

    def __init__(self, session_data={}):
        self._setup_checks()
        super().__init__(session_data=session_data)

    def std_queryset(self, **kwargs):
        self.add_satellite_fields_annotations(
            self.static_satellite_class,
            ["file_name", "file_type", "upload_status", "upload_message", "created_at"],
        )
        self.rename_field("created_at", "static_satellite_created_at")
        self.annotations.pop("created_at")
        self.add_linked_satellites_field_annotations(
            FileUploadFileStaticSatellite,
            self.link_file_upload_registry_file_upload_file_class,
            ["file"],
        )
        queryset = self.build_queryset().order_by("-created_at")
        return queryset

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
            is NotImplementedLinkFileUploadRegistryFileUploadFile
        ):
            raise NotImplementedError(
                "FileUploadRegistryRepository class must have link_file_upload_registry_file_upload_file that is not NotImplementedLinkFileUploadRegistryFileUploadFile"
            )

    def get_file_from_registry(self, file_upload_registry_id: int, request) -> TextIO:
        file_upload_registry_path = (
            self.std_queryset().get(pk=file_upload_registry_id).file
        )
        file_upload_registry_path = os.path.join(MEDIA_ROOT, file_upload_registry_path)
        if not os.path.exists(file_upload_registry_path):
            messages.error(request, f"File {file_upload_registry_path} not found")
            return None

        uploaded_file = open(file_upload_registry_path, "rb")
        return uploaded_file


class FileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = FileUploadRegistryHub
    static_satellite_class = FileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        LinkFileUploadRegistryFileUploadFile
    )
