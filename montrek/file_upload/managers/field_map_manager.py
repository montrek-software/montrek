from dataclasses import dataclass
import pandas as pd
from file_upload.repositories.field_map_repository import FieldMapRepository


@dataclass
class FieldMapExceptionInfo:
    function_name: str
    source_field: str
    database_field: str
    exception_message: str


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

    def __init__(self):
        self._reset_exceptions()

    def _reset_exceptions(self):
        self.exceptions = []

    def apply_field_maps(self, source_df: pd.DataFrame) -> pd.DataFrame:
        self._reset_exceptions()
        field_maps = (
            self.field_map_repository_class()
            .std_queryset()
            .filter(source_field__in=source_df.columns.to_list())
        )
        mapped_df = pd.DataFrame()
        for field_map in field_maps:
            func = getattr(
                self.field_map_function_manager_class, field_map.function_name
            )
            function_parameters = field_map.function_parameters or {}
            try:
                mapped_df[field_map.database_field] = func(
                    source_df, field_map.source_field, **function_parameters
                )
            except Exception as e:
                exception_info = FieldMapExceptionInfo(
                    source_field=field_map.source_field,
                    database_field=field_map.database_field,
                    function_name=field_map.function_name,
                    exception_message=f"{e.__class__.__name__}: {e}",
                )
                self.exceptions.append(exception_info)

        return mapped_df
