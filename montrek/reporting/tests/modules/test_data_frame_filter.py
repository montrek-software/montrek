import datetime
from decimal import Decimal

import pandas as pd
from django.test import SimpleTestCase

from reporting.modules.data_frame_filter import DataFrameFilter, DataFrameFilterError


def condition(value, negate=False) -> dict:
    return {"filter_value": value, "filter_negate": negate}


class TestDataFrameFilter(SimpleTestCase):
    def setUp(self):
        records = [
            {
                "name": "Alpha",
                "count": 1,
                "ratio": 0.5,
                "amount": Decimal("10.5"),
                "day": datetime.date(2026, 1, 1),
                "moment": datetime.datetime(2026, 1, 1, 12),
                "active": True,
                "rank": 1,
                "stamp": datetime.datetime(2026, 1, 1, 12, tzinfo=datetime.UTC),
            },
            {
                "name": "beta",
                "count": 2,
                "ratio": 1.5,
                "amount": Decimal("20"),
                "day": datetime.date(2026, 2, 1),
                "moment": datetime.datetime(2026, 2, 1, 12),
                "active": False,
                "rank": None,
                "stamp": datetime.datetime(2026, 2, 1, 12, tzinfo=datetime.UTC),
            },
            {
                "name": None,
                "count": 3,
                "ratio": None,
                "amount": None,
                "day": None,
                "moment": None,
                "active": True,
                "rank": 3,
                "stamp": None,
            },
        ]
        # As the manager builds it, so that each column keeps its types
        self.df = pd.DataFrame(records, dtype=object)

    def rows(self, filter_dict: dict) -> list[int]:
        mask = DataFrameFilter(filter_dict).mask(self.df)
        return list(self.df.index[mask])

    def test_no_filter_keeps_all_rows(self):
        self.assertEqual(self.rows({}), [0, 1, 2])

    def test_exact_is_case_sensitive(self):
        self.assertEqual(self.rows({"name__exact": condition("Alpha")}), [0])
        self.assertEqual(self.rows({"name__exact": condition("alpha")}), [])

    def test_key_without_lookup_is_exact(self):
        self.assertEqual(self.rows({"name": condition("beta")}), [1])

    def test_iexact(self):
        self.assertEqual(self.rows({"name__iexact": condition("ALPHA")}), [0])

    def test_contains_startswith_endswith(self):
        self.assertEqual(self.rows({"name__contains": condition("et")}), [1])
        self.assertEqual(self.rows({"name__startswith": condition("Al")}), [0])
        self.assertEqual(self.rows({"name__endswith": condition("ta")}), [1])

    def test_contains_is_no_regular_expression(self):
        self.assertEqual(self.rows({"name__contains": condition(".*")}), [])

    def test_comparisons_convert_the_value_to_the_column_type(self):
        self.assertEqual(self.rows({"count__gt": condition("1")}), [1, 2])
        self.assertEqual(self.rows({"count__gte": condition("2")}), [1, 2])
        self.assertEqual(self.rows({"ratio__lt": condition("1")}), [0])
        self.assertEqual(self.rows({"amount__lte": condition("10.5")}), [0])
        self.assertEqual(self.rows({"day__gte": condition("2026-02-01")}), [1])
        self.assertEqual(self.rows({"moment__lt": condition("2026-01-15")}), [0])

    def test_in(self):
        self.assertEqual(self.rows({"count__in": condition(["1", "3"])}), [0, 2])
        self.assertEqual(self.rows({"name__in": condition(["beta", "x"])}), [1])

    def test_boolean(self):
        self.assertEqual(self.rows({"active__exact": condition(False)}), [1])
        self.assertEqual(self.rows({"active__exact": condition("True")}), [0, 2])

    def test_isnull(self):
        self.assertEqual(self.rows({"name__isnull": condition(True)}), [2])
        self.assertEqual(self.rows({"name__isnull": condition(False)}), [0, 1])
        self.assertEqual(self.rows({"name__isnull": condition(True, True)}), [0, 1])

    def test_negation_keeps_empty_values(self):
        self.assertEqual(self.rows({"name__exact": condition("Alpha", True)}), [1, 2])
        self.assertEqual(self.rows({"ratio__gt": condition("1", True)}), [0, 2])

    def test_negation_of_a_column_without_values_keeps_all_rows(self):
        df = pd.DataFrame({"name": [None, None]}, dtype=object)
        mask = DataFrameFilter({"name__exact": condition("x", True)}).mask(df)
        self.assertEqual(list(mask), [True, True])

    def test_text_lookups_compare_the_text(self):
        self.assertEqual(self.rows({"ratio__contains": condition("5")}), [0, 1])
        self.assertEqual(self.rows({"day__startswith": condition("2026-02")}), [1])
        self.assertEqual(self.rows({"count__iexact": condition("2")}), [1])

    def test_ints_with_an_empty_value_stay_ints(self):
        self.assertEqual(self.rows({"rank__exact": condition("3")}), [2])
        with self.assertRaises(DataFrameFilterError):
            self.rows({"rank__in": condition(["1.0", "2"])})

    def test_naive_value_on_an_aware_column_is_in_the_default_time_zone(self):
        self.assertEqual(self.rows({"stamp__lt": condition("2026-01-15")}), [0])
        self.assertEqual(
            self.rows({"stamp__exact": condition("2026-02-01 12:00+00:00")}), [1]
        )

    def test_all_conditions_must_hold(self):
        filter_dict = {
            "active__exact": condition(True),
            "count__gt": condition("1"),
        }
        self.assertEqual(self.rows(filter_dict), [2])

    def test_or_group(self):
        filter_dict = {
            "OR": {
                "name__exact": condition("Alpha"),
                "count__exact": condition("3"),
            },
            "active__exact": condition(True),
        }
        self.assertEqual(self.rows(filter_dict), [0, 2])

    def test_empty_or_group_keeps_all_rows(self):
        self.assertEqual(self.rows({"OR": {}}), [0, 1, 2])

    def test_unknown_column(self):
        with self.assertRaisesRegex(DataFrameFilterError, "Cannot resolve keyword"):
            self.rows({"unknown__exact": condition("x")})

    def test_value_that_does_not_fit_the_column(self):
        for key, value in (
            ("count__exact", "1.0"),
            ("count__in", ["1.0", "2"]),
            ("amount__gt", "ten"),
            ("day__gt", "yesterday"),
            ("active__exact", "maybe"),
        ):
            with self.subTest(key=key), self.assertRaises(DataFrameFilterError):
                self.rows({key: condition(value)})

    def test_column_without_values(self):
        df = pd.DataFrame({"name": [None, None]})
        mask = DataFrameFilter({"name__exact": condition("x")}).mask(df)
        self.assertEqual(list(mask), [False, False])
