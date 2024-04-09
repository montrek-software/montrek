import logging
import pandas as pd
from file_upload.managers.field_map_file_upload_processor import (
    FieldMapFileUploadProcessor,
)


from montrek_example.repositories.hub_a_repository import HubARepository

logger = logging.getLogger(__name__)


class A1FileUploadProcessor(FieldMapFileUploadProcessor):
    message = "Not implemented"
    repository_class = HubARepository

    @classmethod
    def _get_source_df_from_file(cls, file_path):
        return pd.read_csv(file_path)
