import pandas as pd
import numpy as np
from django.test import TestCase, override_settings

from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from file_upload.managers.field_map_manager import (
    FieldMapFunctionManager,
    FieldMapManager,
)


class MyFieldMapFunctionManager(FieldMapFunctionManager):
    @staticmethod
    def append_source_field_1(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        return source_df[source_field].astype(str) + source_df["source_field_1"]

    @staticmethod
    def raise_error(source_df: pd.DataFrame, source_field: str) -> pd.Series:
        raise RuntimeError("bad error")


class MyFieldMapManager(FieldMapManager):
    field_map_function_manager_class = MyFieldMapFunctionManager


class TestFieldMapManager(TestCase):
    def setUp(self):
        self.source_df = pd.DataFrame(
            {
                "source_field_0": [1, 2, 3],
                "source_field_1": ["a", "b", "c"],
                "source_field_2": [4, 5, 6],
                "source_field_3": [7, 8, 9],
            }
        )

    def test_apply_field_maps(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0", database_field="database_field_0"
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_1", database_field="database_field_1"
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_2",
            database_field="database_field_2",
            function_name="multiply_by_value",
            function_parameters={"value": 2},
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_3",
            database_field="database_field_3",
            function_name="append_source_field_1",
        )

        field_map_manager = MyFieldMapManager({})
        mapped_df = field_map_manager.apply_field_maps(self.source_df)

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
        self.assertEqual(field_map_manager.exceptions, [])

    @override_settings(IS_TEST_RUN=False)
    def test_apply_field_maps_exception(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="database_field_0",
            function_name="raise_error",
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_1", database_field="database_field_1"
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_2",
            database_field="database_field_2",
            function_name="raise_error",
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_3",
            database_field="database_field_3",
            function_name="append_source_field_1",
        )

        field_map_manager = MyFieldMapManager({})
        mapped_df = field_map_manager.apply_field_maps(self.source_df)

        exceptions = field_map_manager.exceptions
        self.assertEqual(len(exceptions), 2)
        self.assertEqual(exceptions[0].function_name, "raise_error")
        self.assertEqual(exceptions[0].source_field, "source_field_0")
        self.assertEqual(exceptions[0].database_field, "database_field_0")
        self.assertEqual(exceptions[0].function_parameters, {})
        self.assertEqual(exceptions[0].exception_message, "RuntimeError: bad error")
        self.assertEqual(exceptions[1].function_name, "raise_error")
        self.assertEqual(exceptions[1].source_field, "source_field_2")
        self.assertEqual(exceptions[1].database_field, "database_field_2")
        self.assertEqual(exceptions[1].function_parameters, {})
        self.assertEqual(exceptions[1].exception_message, "RuntimeError: bad error")

        self.assertEqual(
            mapped_df.columns.to_list(),
            [
                "database_field_1",
                "database_field_3",
            ],
        )
        self.assertEqual(mapped_df["database_field_1"].to_list(), ["a", "b", "c"])
        self.assertEqual(mapped_df["database_field_3"].to_list(), ["7a", "8b", "9c"])

    def test_get_source_field_from_database_field(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0", database_field="database_field_0"
        )
        field_map_manager = MyFieldMapManager({})
        test_source_field = field_map_manager.get_source_field_from_database_field(
            "database_field_0"
        )
        self.assertEqual(test_source_field, "source_field_0")
        with self.assertRaises(ValueError):
            test_source_field = field_map_manager.get_source_field_from_database_field(
                "database_field_1"
            )


class TestFieldMapFunctionManager(TestCase):
    def setUp(self):
        self.source_df = pd.DataFrame(
            {
                "source_field_0": [
                    1,
                    "2",
                    "a3",
                    "4b",
                    "c5d",
                    "6e7f",
                    "g",
                    "h8.5",
                    None,
                    "asdj-3.14159akcjnb",
                ],
            }
        )

    def test_extract_number(self):
        result = FieldMapFunctionManager.extract_number(
            self.source_df, "source_field_0"
        )
        expected = pd.Series(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                np.nan,
                8.5,
                np.nan,
                -3.14159,
            ]
        )
        assert result.equals(expected)
