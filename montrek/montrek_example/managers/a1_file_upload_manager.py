import pandas as pd
import logging

from typing import Dict, Any


from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from montrek_example.managers.a1_field_map_manager import A1FieldMapManager
from montrek_example.repositories.hub_a_repository import HubARepository

logger = logging.getLogger(__name__)


class AFileUploadProcessor:
    message = "Not implemented"
    file_upload_registry = None

    def __init__(
        self, file_upload_registry_id: int, session_data: Dict[str, Any], **kwargs
    ):
        self.session_data = session_data
        self.file_upload_registry_id = file_upload_registry_id
        self.file_upload_registry_repository = FileUploadRegistryRepository(
            session_data
        )
        self.hub_a_repository = HubARepository(session_data)
        self.file_upload_registry_hub = (
            self.file_upload_registry_repository.std_queryset().get(
                pk=file_upload_registry_id
            )
        )

    def process(self, file_path: str):
        source_df = pd.read_csv(file_path)
        mapped_df = A1FieldMapManager.apply_field_maps(source_df)
        mapped_df["comment"] = self.file_upload_registry_hub.file_name
        mapped_df["link_hub_a_file_upload_registry"] = self.file_upload_registry_hub
        self.hub_a_repository.create_objects_from_data_frame(mapped_df)
        self.message = f"Successfully uploaded {mapped_df.shape[0]} rows."
        return True

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True
