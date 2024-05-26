from dataclasses import dataclass
import pandas as pd
from file_upload.repositories.field_map_repository import (
    FieldMapRepositoryABC,
)
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.dataclasses.table_elements import StringTableElement


@dataclass
class FieldMapExceptionInfo:
    database_field: str
    exception_message: str
    function_name: str
    function_parameters: dict
    source_field: str


class FieldMapFunctionManager:
    @staticmethod
    def no_change(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field]

    @staticmethod
    def multiply_by_value(
        source_df: pd.DataFrame, source_field: str, value: float
    ) -> pd.Series:
        return source_df[source_field].multiply(value)


class FieldMapManagerABC(MontrekTableManager):
    field_map_function_manager_class = FieldMapFunctionManager
    repository_class = FieldMapRepositoryABC

    @property
    def table_elements(self) -> list:
        return [
            StringTableElement(name="Source Field", attr="source_field"),
            StringTableElement(name="Database Field", attr="database_field"),
            StringTableElement(name="Function Name", attr="function_name"),
            StringTableElement(name="Function Parameters", attr="function_parameters"),
            StringTableElement(
                name="Comment", attr="field_map_static_satellite_comment"
            ),
        ]

    def __init__(self, session_data: dict):
        self._reset_exceptions()
        super().__init__(session_data=session_data)

    def _reset_exceptions(self):
        self.exceptions = []

    def apply_field_maps(self, source_df: pd.DataFrame) -> pd.DataFrame:
        self._reset_exceptions()
        field_maps = self.repository.std_queryset().filter(
            source_field__in=source_df.columns.to_list()
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
                    database_field=field_map.database_field,
                    exception_message=f"{e.__class__.__name__}: {e}",
                    function_name=field_map.function_name,
                    function_parameters=function_parameters,
                    source_field=field_map.source_field,
                )
                self.exceptions.append(exception_info)

        return mapped_df
