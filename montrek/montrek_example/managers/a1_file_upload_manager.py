import logging
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.managers.file_upload_manager_mixins import LogFileMixin
from montrek_example.managers.a_upload_table_manager import (
    HubAFileUploadRegistryManager,
)
import pandas as pd
from file_upload.managers.field_map_file_upload_processor import (
    FieldMapFileUploadProcessor,
)
from montrek_example.managers.a1_field_map_manager import A1FieldMapManager
from montrek_example.managers.montrek_example_managers import HubAManager


logger = logging.getLogger(__name__)


class A1FileUploadProcessor(FieldMapFileUploadProcessor, LogFileMixin):
    message = "Not implemented"
    manager_class = HubAManager
    field_map_manager_class = A1FieldMapManager

    @classmethod
    def get_source_df_from_file(cls, file_path):
        return pd.read_csv(file_path)

    def add_link_columns(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        mapped_df["link_hub_a_file_upload_registry"] = self.file_upload_registry_hub
        return mapped_df

    def post_map_processing(self, mapped_df: pd.DataFrame) -> pd.DataFrame:
        merged_df = super().post_map_processing(mapped_df)
        self.generate_log_file_excel(
            f"Mapped input data",
            additional_data=merged_df,
        )
        return merged_df


class A1FileUploadManager(FileUploadManagerABC):
    file_upload_processor_class = A1FileUploadProcessor
    file_registry_manager_class = HubAFileUploadRegistryManager
