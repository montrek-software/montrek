from dataclasses import dataclass
import pandas as pd
from file_upload.repositories.field_map_repository import (
    FieldMapRepository,
    FieldMapRepositoryABC,
)
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.dataclasses.table_elements import (
    IntTableElement,
    LinkTableElement,
    StringTableElement,
    TableElement,
    MethodNameTableElement,
)


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
        """
        Returns the data series from the source DataFrame without any changes.

        Parameters:
        source_df (pd.DataFrame): The source DataFrame (passed automatically).
        source_field (str): The field to be returned.

        Returns:
        pd.Series: The data series corresponding to the source_field.
        """
        return source_df[source_field]

    @staticmethod
    def multiply_by_value(
        source_df: pd.DataFrame, source_field: str, value: float
    ) -> pd.Series:
        """
        Returns a data series that is the result of multiplying the source_field
        by a value.

        Parameters:
        source_df (pd.DataFrame): The source DataFrame (passed automatically).
        source_field (str): The field to be multiplied.
        value (float): The value to multiply by.

        example function_parameters: {"value": 2}

        Returns:
        pd.Series: The data series resulting from the multiplication.
        """
        return source_df[source_field].multiply(value)

    @staticmethod
    def extract_number(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        """
        Returns a data series that is the result of extracting the first number
        from each string in the source_field.

        Parameters:
        source_df (pd.DataFrame): The source DataFrame (passed automatically).
        source_field (str): The string field from which to extract numbers.

        Returns:
        pd.Series: The series of extracted numbers as floats.
        """
        str_series = source_df[source_field].astype(str)
        pattern = r"(-?\d+\.\d+|-?\d+)"
        group_match_df = str_series.str.extract(pattern)
        result_series = group_match_df[0].astype(float)
        return result_series


class FieldMapManagerABC(MontrekTableManager):
    field_map_function_manager_class = FieldMapFunctionManager
    repository_class = FieldMapRepositoryABC
    update_url = ""
    delete_url = ""

    @property
    def table_elements(self) -> tuple[TableElement, ...]:
        return (
            StringTableElement(name="Source Field", attr="source_field"),
            StringTableElement(name="Database Field", attr="database_field"),
            IntTableElement(name="Step", attr="step"),
            MethodNameTableElement(
                name="Function Name",
                attr="function_name",
                class_=self.field_map_function_manager_class,
            ),
            StringTableElement(name="Function Parameters", attr="function_parameters"),
            StringTableElement(
                name="Comment", attr="field_map_static_satellite_comment"
            ),
            LinkTableElement(
                name="Edit",
                url=self.update_url,
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Edit Field Map",
            ),
            LinkTableElement(
                name="Delete",
                url=self.delete_url,
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Field Map",
            ),
        )

    def __init__(self, session_data: dict):
        self._reset_exceptions()
        super().__init__(session_data=session_data)

    def _reset_exceptions(self):
        self.exceptions = []

    def get_field_map(self, source_df: pd.DataFrame) -> pd.DataFrame:
        field_maps = self.repository.std_queryset().filter(
            source_field__in=source_df.columns.to_list()
        )
        return field_maps

    def apply_field_maps(self, source_df: pd.DataFrame) -> pd.DataFrame:
        self._reset_exceptions()
        mapped_df = pd.DataFrame()
        field_maps = self.get_field_map(source_df)
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

    def get_source_field_from_database_field(self, database_field: str) -> str:
        source_field = self.repository.get_source_field(database_field)
        if not source_field:
            raise ValueError(
                f"No source field found for database field {database_field}"
            )
        return source_field


class FieldMapManager(FieldMapManagerABC):
    repository_class = FieldMapRepository
