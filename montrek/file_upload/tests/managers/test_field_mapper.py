import pandas as pd
from django.test import TestCase

from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from file_upload.managers.field_mapper import FieldMapManager


class MyFieldMapManager(FieldMapManager):
    def fn_multiply_by_2(self, source_field: str) -> pd.Series:
        return self.source_df[source_field] * 2

    def fn_append_source_field_1(self, source_field: str) -> pd.Series:
        return (
            self.source_df[source_field].astype(str) + self.source_df["source_field_1"]
        )


class TestFieldMapManager(TestCase):
    def test_apply_field_maps(self):
        FieldMapStaticSatelliteFactory(source_field="source_field_0")
        FieldMapStaticSatelliteFactory(source_field="source_field_1")
        FieldMapStaticSatelliteFactory(
            source_field="source_field_2", function_name="fn_multiply_by_2"
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_3", function_name="fn_append_source_field_1"
        )

        source_df = pd.DataFrame(
            {
                "source_field_0": [1, 2, 3],
                "source_field_1": ["a", "b", "c"],
                "source_field_2": [4, 5, 6],
                "source_field_3": [7, 8, 9],
            }
        )

        field_mapper = MyFieldMapManager(source_df)
        mapped_df = field_mapper.apply_field_maps()

        self.assertEqual(
            mapped_df.columns.to_list(),
            [
                "database_field_0",
                "database_field_1",
                "database_field_2",
                "database_field_3",
            ],
        )
        self.assertEqual(mapped_df["database_field_0"].to_list(), [1, 2, 3])
        self.assertEqual(mapped_df["database_field_1"].to_list(), ["a", "b", "c"])
        self.assertEqual(mapped_df["database_field_2"].to_list(), [8, 10, 12])
        self.assertEqual(mapped_df["database_field_3"].to_list(), ["7a", "8b", "9c"])
