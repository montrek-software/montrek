import pandas as pd
import numpy as np
import logging

from typing import Dict, Any


from file_upload.models import FileUploadRegistryHubABC
from baseclasses.managers.montrek_manager import MontrekManager
from file_upload.managers.field_map_manager import (
    FieldMapManagerABC,
)

logger = logging.getLogger(__name__)


class FieldMapFileUploadProcessor:
    message = "Not implemented"
    detailed_message = ""
    manager_class: type[MontrekManager] | None = None
    field_map_manager_class: type[FieldMapManagerABC] = FieldMapManagerABC

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: Dict[str, Any],
        **kwargs,
    ):
        self.session_data = session_data

        if not self.manager_class:
            raise ValueError("manager_class must be set in subclass.")
        self.manager = self.manager_class(self.session_data)
        self.file_upload_registry_hub = file_upload_registry_hub

    def get_source_df_from_file(self, file_path: str) -> pd.DataFrame:
        NotImplementedError("Please implement this method in a subclass.")

    def add_link_columns(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        NotImplementedError("Please implement this method in a subclass.")

    def post_map_processing(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        return mapped_df

    def process(self, file_path: str):
        source_df = self.get_source_df_from_file(file_path)

        field_map_manager = self.field_map_manager_class(self.session_data)
        mapped_df = field_map_manager.apply_field_maps(source_df)
        if field_map_manager.exceptions:
            self.message = "Errors raised during field mapping:"
            for e in field_map_manager.exceptions:
                self.message += f"<br>{e.source_field, e.database_field, e.function_name, e.function_parameters, e.exception_message}"
            return False
        try:
            mapped_df["comment"] = self.file_upload_registry_hub.file_name
            mapped_df = self.add_link_columns(mapped_df)
            mapped_df = mapped_df.replace({np.nan: None})
            mapped_df = self.post_map_processing(mapped_df)
            self.manager.repository.create_objects_from_data_frame(mapped_df)
        except Exception as e:
            self.message = (
                f"Error raised during object creation: <br>{e.__class__.__name__}: {e}"
            )
            return False
        for message in self.manager.repository.messages:
            self.detailed_message += f"<br>{message.message}<br>"

        self.message = (
            f"Successfully uploaded {mapped_df.shape[0]} rows.{self.detailed_message}"
        )
        return True

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True
