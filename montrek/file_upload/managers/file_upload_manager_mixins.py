from django.core.files import File
from django.utils import timezone
import pandas as pd
from io import BytesIO
from file_upload.repositories.file_upload_file_repository import (
    FileUploadFileRepository,
)


class LogFileChecksMixin:
    def _check_attributes(self):
        if not hasattr(self, "file_upload_registry_hub"):
            raise AttributeError(
                "ExcelLogFileMixin has no file_upload_registry_hub attribute.",
            )
        if not hasattr(self, "log_link_name"):
            raise AttributeError(
                "ExcelLogFileMixin has no log_link_name attribute.",
            )
        if not hasattr(self, "session_data"):
            raise AttributeError(
                "ExcelLogFileMixin has no session_data attribute.",
            )


class LogFileMixin(LogFileChecksMixin):
    def generate_log_file_excel(
        self, message: str, *, additional_data: pd.DataFrame | None = None
    ):
        self._check_attributes()
        excel_log_file = self._generate_excel_file(message, additional_data)
        self._add_log_file_link(excel_log_file)

    def _generate_excel_file(
        self, message: str, additional_data: pd.DataFrame | None
    ) -> File:
        file_name = "upload_log.xlsx"
        log_sr = pd.Series(
            {
                "Upload Message": message,
                "Upload Date": self.file_upload_registry_hub.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Uploaded By": self.file_upload_registry_hub.created_by,
            },
            name="Log Meta Data",
        )
        log_sr.index.name = "Param"
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as excel_writer:
            log_sr.to_excel(excel_writer, "meta_data")
            if isinstance(additional_data, pd.DataFrame):
                additional_data.to_excel(excel_writer, "additional_data", index=False)
        excel_log_file = File(buffer, name=file_name)
        return excel_log_file

    def _add_log_file_link(self, file: File):
        file_log_hub = FileUploadFileRepository(self.session_data).std_create_object(
            {"file": file}
        )
        registry_log_file_link = getattr(
            self.file_upload_registry_hub, self.log_link_name
        )
        registry_log_file_link.add(file_log_hub)
