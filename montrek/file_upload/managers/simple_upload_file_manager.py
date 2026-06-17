from typing import Any

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.urls import resolve

from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.managers.file_upload_manager import (
    FileUploadManagerABC,
    FileUploadProcessorProtocol,
)
from file_upload.models import FileUploadRegistryHubABC
from reporting.managers.montrek_table_manager import MontrekTableManagerABC


class SimpleFileUploadProcessor(FileUploadProcessorProtocol):
    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: dict[str, Any],
        **kwargs: Any,
    ):
        view_class = resolve(session_data["request_path"]).func.view_class
        self.table_manager: MontrekTableManagerABC = view_class.manager_class(
            session_data
        )
        self.overwrite: bool = session_data["overwrite"]
        self.input_df: pd.DataFrame | None = None
        self.target_repository: MontrekRepository | None = None

    def pre_check(self, file_path: str) -> bool:
        file_type = file_path.split(".")[-1]
        if file_type == "csv":
            input_df = pd.read_csv(file_path)
        elif file_type == "xlsx":
            input_df = pd.read_excel(file_path)
        else:
            self.set_message(f"File type {file_type} not supported")
            return False
        name_to_field_map = self.table_manager.get_table_elements_name_to_field_map()
        field_to_name_map = {v: k for k, v in name_to_field_map.items()}
        self.input_df = input_df.rename(columns=name_to_field_map)
        self.target_repository = self.table_manager.repository
        has_all_id_fields = True
        for id_field in self.target_repository.get_identifier_fields():
            if id_field not in self.input_df.columns:
                display_name = field_to_name_map.get(id_field, id_field)
                self.set_message(self.message + f"{display_name} not in input data")
                has_all_id_fields = False

        return has_all_id_fields

    def process(self, _: str) -> bool:
        if self.target_repository is None or self.input_df is None:
            self.set_message("pre_check must run before process")
            return False
        try:
            if self.overwrite:
                with transaction.atomic():
                    for obj in self.target_repository.receive():
                        self.target_repository.delete(obj.hub)
                    self.target_repository.create_objects_from_data_frame(self.input_df)
            else:
                self.target_repository.create_objects_from_data_frame(self.input_df)
        except Exception as e:
            if settings.IS_TEST_RUN:
                raise e
            self.set_message(str(e))
            return False

        return True

    def post_check(self, _: str) -> bool:
        return True


class SimpleUploadFileManager(FileUploadManagerABC):
    file_upload_processor_class = SimpleFileUploadProcessor
    do_process_file_async = False
