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
