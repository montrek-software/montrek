import os
from typing import TextIO
from django.utils import timezone
from django.contrib import messages
from montrek.settings import MEDIA_ROOT
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import LinkFileUploadRegistryFileUploadFile


class FileUploadRegistryRepository(MontrekRepository):
    hub_class = FileUploadRegistryHub

    def std_queryset(self, **kwargs):
        self.add_satellite_fields_annotations(
            FileUploadRegistryStaticSatellite,
            ["file_name", "file_type", "upload_status", "upload_message"],
        )
        self.add_linked_satellites_field_annotations(
            FileUploadFileStaticSatellite,
            LinkFileUploadRegistryFileUploadFile,
            ["file"],
        )
        queryset = self.build_queryset().order_by("-created_at")
        return queryset

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
