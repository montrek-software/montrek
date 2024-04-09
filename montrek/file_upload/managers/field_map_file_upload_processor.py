import pandas as pd
import logging

from typing import Dict, Any


from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from montrek_example.managers.a1_field_map_manager import A1FieldMapManager

logger = logging.getLogger(__name__)


class FieldMapFileUploadProcessor:
    message = "Not implemented"
    repository_class = None

    def __init__(
        self, file_upload_registry_id: int, session_data: Dict[str, Any], **kwargs
    ):
        self.session_data = session_data
        self.file_upload_registry_id = file_upload_registry_id
        self.file_upload_registry_repository = FileUploadRegistryRepository(
            session_data
        )
        self.repository = self.repository_class(session_data)
        self.file_upload_registry_hub = (
            self.file_upload_registry_repository.std_queryset().get(
                pk=file_upload_registry_id
            )
        )

    def _get_source_df_from_file(self, file_path: str) -> pd.DataFrame:
        NotImplementedError("Please implement this method in a subclass.")

    def process(self, file_path: str):
        source_df = self._get_source_df_from_file(file_path)
        field_map_manager = A1FieldMapManager()
        mapped_df = field_map_manager.apply_field_maps(source_df)
        if field_map_manager.exceptions:
            self.message = "Errors raised during field mapping:"
            for e in field_map_manager.exceptions:
                self.message += f"<br>{e.source_field, e.database_field, e.function_name, e.function_parameters, e.exception_message}"
            return False
        try:
            mapped_df["comment"] = self.file_upload_registry_hub.file_name
            mapped_df["link_hub_a_file_upload_registry"] = self.file_upload_registry_hub
            self.repository.create_objects_from_data_frame(mapped_df)
        except Exception as e:
            self.message = f"Error raised during object creation: {e}"
            return False
        self.message = f"Successfully uploaded {mapped_df.shape[0]} rows."
        return True

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True
