import pandas as pd
from file_upload.repositories.field_map_repository import FieldMapRepository


class FieldMapFunctionManager:
    @staticmethod
    def no_change(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field]


class FieldMapManager:
    def __init__(
        self,
        source_df: pd.DataFrame,
        field_map_function_manager: FieldMapFunctionManager,
    ):
        self.source_df = source_df
        self.field_map_function_manager = field_map_function_manager
        self.field_map_repository = FieldMapRepository()
        self.field_maps = self.field_map_repository.std_queryset().filter(
            source_field__in=self.source_df.columns.to_list()
        )

    def apply_field_maps(self):
        mapped_df = pd.DataFrame()
        for field_map in self.field_maps:
            func = getattr(self.field_map_function_manager, field_map.function_name)
            mapped_df[field_map.database_field] = func(
                self.source_df, field_map.source_field
            )
        return mapped_df
