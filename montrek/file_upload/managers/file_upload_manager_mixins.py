import datetime
import re
from django.core.files import File
from django.utils import timezone
import pandas as pd
from io import BytesIO
from file_upload.repositories.file_upload_file_repository import (
    FileUploadFileRepository,
)
from user.repositories.user_repository import MontrekUserRepository


class LogFileChecksMixin:
    def _check_attributes(self):
        if not hasattr(self, "file_upload_registry_hub"):
            raise AttributeError(
                "ExcelLogFileMixin has no file_upload_registry_hub attribute.",
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
        user_mail = (
            MontrekUserRepository()
            .std_queryset()
            .get(id=self.session_data["user_id"])
            .email
        )
        log_sr = pd.Series(
            {
                "Upload Message": message,
                "Upload Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Uploaded By": user_mail,
            },
            name="Log Meta Data",
        )
        log_sr.index.name = "Param"
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as excel_writer:
            log_sr.to_excel(excel_writer, sheet_name="meta_data")
            if isinstance(additional_data, pd.DataFrame):
                for dtype in additional_data.dtypes:
                    if dtype == "object":
                        additional_data = additional_data.astype(str)
                additional_data.to_excel(
                    excel_writer, sheet_name="additional_data", index=False
                )
        excel_log_file = File(buffer, name=file_name)
        return excel_log_file

    def _add_log_file_link(self, file: File):
        registry_log_file_link = (
            self.file_upload_registry_hub.hub.link_file_upload_registry_file_log_file
        )
        create_data = {"file": file}
        now = timezone.make_aware(datetime.datetime.now())
        existing_log_file = registry_log_file_link.filter(
            state_date_end__gt=now, state_date_start__lt=now
        )
        if existing_log_file.exists():
            create_data["hub_entity_id"] = existing_log_file.first().pk
            file.name = LogFileMixin._add_suffix_before_extension(
                str(file.name), f"_{now}"
            )

        file_log_hub = FileUploadFileRepository(self.session_data).std_create_object(
            create_data
        )
        registry_log_file_link.add(file_log_hub)

    @staticmethod
    def _add_suffix_before_extension(filename: str, suffix: str) -> str:
        # Define the regex pattern to find the last period in the filename
        pattern = r"(?=\.[^.]+$)"
        # Substitute the matched pattern with _xxx before the last period
        new_filename = re.sub(pattern, f"{suffix}", filename)
        return new_filename
