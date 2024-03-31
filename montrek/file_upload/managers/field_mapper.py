import pandas as pd
from file_upload.repositories.field_map_repository import FieldMapRepository


class FieldMapper:
    def __init__(self, source_df: pd.DataFrame):
        self.source_df = source_df

        self.field_maps = (
            FieldMapRepository()
            .std_queryset()
            .filter(source_field__in=self.source_df.columns.to_list())
        )

    def apply_field_maps(self):
        mapped_df = pd.DataFrame()
        for field_map in self.field_maps:
            func = getattr(self, field_map.function_name)
            mapped_df[field_map.database_field] = func(field_map.source_field)
        return mapped_df

    def fn_no_change(self, source_field: str) -> pd.Series:
        return self.source_df[source_field]
