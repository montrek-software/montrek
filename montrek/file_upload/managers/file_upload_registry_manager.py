from django.core.files import File
from baseclasses.errors.montrek_user_error import MontrekError
from django.http import FileResponse
from django.http.response import HttpResponseBase
from file_upload.constants import UploadStatus
from process_pipeline.managers.pipeline_registry_manager import (
    PipelineRegistryManagerABC,
)
from reporting.dataclasses.table_elements import StringTableElement

from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
    FileUploadRegistryRepositoryABC,
)


class FileUploadRegistryManagerABC(PipelineRegistryManagerABC):
    repository_class = FileUploadRegistryRepositoryABC
    registry_status_text_choices = UploadStatus
    download_url = "please define download_url in subclass"
    download_log_url = ""
    history_url = ""

    status_attr = "upload_status"
    message_attr = "upload_message"
    status_column_name = "Upload Status"
    message_column_name = "Upload Message"
    date_attr = "upload_date"
    date_column_name = "Upload Date"
    created_by_column_name = "Uploaded By"
    download_column_name = "File"
    revoke_url = "revoke_file_upload_task"
    revoke_hover_text = "Revoke Upload Task"
    # Repository method that returns the file to download for the registry ``pk``.
    get_file_method = "get_upload_file_from_registry"
    _download_file: File | None = None

    def download(self) -> HttpResponseBase:
        return FileResponse(self.download_file)

    def get_filename(self) -> str:
        return str(self.download_file.name)

    @property
    def download_file(self) -> File:
        if self._download_file is None:
            download_file = getattr(self.repository, self.get_file_method)(
                int(self.session_data["pk"])
            )
            if download_file is None:
                raise MontrekError("File Not Found")
            self._download_file = download_file
        return self._download_file

    @property
    def file_name_element(self) -> StringTableElement:
        return StringTableElement(name="File Name", attr="file_name")

    @property
    def table_elements(self) -> tuple:
        return (
            self.file_name_element,
            self.status_element,
            self.message_element,
            self.date_element,
            self.created_by_element,
            self.download_element,
            self.revoke_element,
            *self.optional_elements,
        )


class FileUploadRegistryManager(FileUploadRegistryManagerABC):
    repository_class = FileUploadRegistryRepository
