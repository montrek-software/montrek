import pandas as pd
import logging


from file_upload.managers.field_map_manager import (
    FieldMapFunctionManager,
    FieldMapManagerABC,
)
from montrek_example.repositories.sat_a1_repository import (
    SatA1FieldMapRepository,
)

logger = logging.getLogger(__name__)


class A1FieldMapFunctionManager(FieldMapFunctionManager):
    @staticmethod
    def append_source_field_1(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field].astype(str) + source_df["source_field_1"].astype(
            str
        )


class A1FieldMapManager(FieldMapManagerABC):
    field_map_function_manager_class = A1FieldMapFunctionManager
    repository_class = SatA1FieldMapRepository
    update_url = "montrek_example_a1_field_map_update"
    delete_url = "montrek_example_a1_field_map_delete"
