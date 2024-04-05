import pandas as pd
from file_upload.repositories.field_map_repository import FieldMapRepository


class FieldMapFunctionManager:
    @staticmethod
    def no_change(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field]

    @staticmethod
    def multiply_by_value(
        source_df: pd.DataFrame, source_field: str, value: float
    ) -> pd.Series:
        return source_df[source_field].multiply(value)


class FieldMapManager:
    field_map_function_manager_class = FieldMapFunctionManager
    field_map_repository_class = FieldMapRepository

    @classmethod
    def apply_field_maps(cls, source_df: pd.DataFrame) -> pd.DataFrame:
        field_maps = (
            cls.field_map_repository_class()
            .std_queryset()
            .filter(source_field__in=source_df.columns.to_list())
        )
        mapped_df = pd.DataFrame()
        for field_map in field_maps:
            func = getattr(
                cls.field_map_function_manager_class, field_map.function_name
            )
            function_parameters = field_map.function_parameters or {}
            mapped_df[field_map.database_field] = func(
                source_df, field_map.source_field, **function_parameters
            )
        return mapped_df
