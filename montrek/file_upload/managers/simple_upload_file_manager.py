from typing import Any
import pandas as pd
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from reporting.managers.montrek_table_manager import MontrekTableManager


class SimpleFileUploadProcessor:
    def __init__(
        self,
        file_upload_registry_hub,
        session_data: dict[str, Any],
        table_manager: MontrekTableManager,
        **kwargs,
    ):
        self.message = ""
        self.table_manager = table_manager

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        file_type = file_path.split(".")[-1]
        if file_type == "csv":
            input_df = pd.read_csv(file_path)
        elif file_type == "xlsx":
            input_df = pd.read_excel(file_path)
        else:
            self.message = f"File type {file_type} not supported"
            return False

        return True

    def post_check(self, file_path: str) -> bool:
        return True


class SimpleUploadFileManager(FileUploadManagerABC):
    file_upload_processor_class = SimpleFileUploadProcessor
