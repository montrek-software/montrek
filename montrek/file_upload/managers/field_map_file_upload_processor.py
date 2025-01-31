import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from baseclasses.managers.montrek_manager import MontrekManager
from file_upload.managers.field_map_manager import (
    FieldMapManagerABC,
)
from file_upload.models import FileUploadRegistryHubABC

logger = logging.getLogger(__name__)


class FieldMapFileUploadProcessor:
    message: str = "Not implemented"
    detailed_message: str = ""
    manager_class: type[MontrekManager] | None = None
    field_map_manager_class: type[FieldMapManagerABC] = FieldMapManagerABC
    non_repository_fields: list[str] = []

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
        self.field_map_manager = self.field_map_manager_class(self.session_data)

    def get_source_df_from_file(self, file_path: str) -> pd.DataFrame:
        NotImplementedError("Please implement this method in a subclass.")

    def add_link_columns(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        NotImplementedError("Please implement this method in a subclass.")

    def post_map_processing(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        return mapped_df

    def process(self, file_path: str):
        try:
            source_df = self.get_source_df_from_file(file_path)
        except Exception as e:
            self.message = (
                f"Error raised during file reading: <br>{e.__class__.__name__}: {e}"
            )
            return False

        mapped_df = self.field_map_manager.apply_field_maps(source_df)
        if self.field_map_manager.exceptions:
            self.message = "Errors raised during field mapping:"
            for e in self.field_map_manager.exceptions:
                self.message += f"<br>{e.source_field, e.database_field, e.function_name, e.function_parameters, e.exception_message}"
            return False
        try:
            mapped_df["comment"] = self.file_upload_registry_hub.file_name
            mapped_df = self.add_link_columns(mapped_df)
            mapped_df = mapped_df.replace({np.nan: None})
            mapped_df = self.post_map_processing(mapped_df)
            self.manager.repository.create_objects_from_data_frame(mapped_df)
        except Exception as e:
            logger.error(str(e))
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

    def _check_all_database_fields_allowed(self):
        repository_fields = set(self.manager.repository.get_all_fields())
        field_map_repo = self.field_map_manager.repository
        used_fields = set(field_map_repo.get_all_database_fields())
        intermediate_fields = set(field_map_repo.get_all_intermediate_fields())
        unallowed_used_fields = (
            used_fields
            - repository_fields
            - intermediate_fields
            - set(self.non_repository_fields)
        )
        if unallowed_used_fields:
            self.message = (
                "The following database fields are defined in the field map but are not in the target repository: "
                + ", ".join(sorted(list(unallowed_used_fields)))
            )
            return False
        return True

    def pre_check(self, file_path: str):
        are_database_fields_ok = self._check_all_database_fields_allowed()
        return are_database_fields_ok

    def post_check(self, file_path: str):
        return True
