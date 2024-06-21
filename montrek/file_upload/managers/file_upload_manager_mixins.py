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


class ExcelLogFileMixin(LogFileChecksMixin):
    def generate_log_file_excel(self, message: str):
        self._check_attributes()
