import pandas as pd
import logging


from file_upload.managers.field_map_manager import (
    FieldMapFunctionManager,
    FieldMapManager,
)
from montrek_example.models import SatA1

logger = logging.getLogger(__name__)


class AFieldMapFunctionManager(FieldMapFunctionManager):
    @staticmethod
    def append_source_field_1(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field].astype(str) + source_df["source_field_1"].astype(
            str
        )

    @staticmethod
    def multiply_by_1000(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field] * 1000


class AFieldMapManager(FieldMapManager):
    satellite_class = SatA1
    field_map_function_manager_class = AFieldMapFunctionManager
