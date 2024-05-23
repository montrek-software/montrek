import pandas as pd
import logging


from file_upload.managers.field_map_manager import (
    FieldMapFunctionManager,
    FieldMapManager,
)

logger = logging.getLogger(__name__)


class A1FieldMapFunctionManager(FieldMapFunctionManager):
    @staticmethod
    def append_source_field_1(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field].astype(str) + source_df["source_field_1"].astype(
            str
        )

    @staticmethod
    def multiply_by_1000(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field] * 1000


class A1FieldMapManager(FieldMapManager):
    field_map_function_manager_class = A1FieldMapFunctionManager
