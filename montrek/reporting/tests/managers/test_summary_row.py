import pandas as pd
from bs4 import BeautifulSoup
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories
from reporting.dataclasses import table_elements as te
from reporting.dataclasses.summary_row_config import SummaryRowConfig
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.tests.mocks import (
    MockLongSummaryRowTableManager,
    MockMontrekTableManager,
    MockSummaryRowDataFrameTableManager,
    MockSummaryRowTableManager,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class DoubledIntTableElement(te.IntTableElement):
    def get_value(self, obj):
        value = super().get_value(obj)
        return value * 2 if isinstance(value, int) else value


class HubCSummaryTableManager(MontrekTableManager):
    repository_class = HubCRepository
    show_summary_row = True

    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Count", attr="field_tsc3_int"),
            te.PercentTableElement(name="Share", attr="field_tsc3_int"),
        )


class HubCComputedSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            DoubledIntTableElement(name="Doubled", attr="field_tsc3_int"),
        )


class HubCSameFieldSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Count", attr="field_tsc3_int"),
            DoubledIntTableElement(name="Doubled", attr="field_tsc3_int"),
        )


class HubCFloatColumnSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Whole", attr="field_tsc2_float"),
            te.FloatTableElement(name="Exact", attr="field_tsc2_float"),
        )


class MockSameFieldSummaryTableManager(MockSummaryRowTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_a"),
            te.IntTableElement(name="Count", attr="field_b"),
            DoubledIntTableElement(name="Doubled", attr="field_b"),
        )


class HubASummaryTableManager(MontrekTableManager):
    repository_class = HubARepository
    show_summary_row = True

    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_a1_str"),
            te.IntTableElement(name="Count", attr="field_a1_int"),
            te.FloatTableElement(name="Amount", attr="field_a2_float"),
        )


def cells(fields) -> list:
    return [(field.name, field.display_value, field.value) for field in fields]


class TestSummaryRowOfMockRows(TestCase):
    def test_sums_the_numeric_columns(self):
        manager = MockSummaryRowTableManager()
        fields = manager.get_summary_fields(manager.table_elements)

        values = {field.name: field.value for field in fields}
        self.assertEqual(values["Field B"], 6)
        self.assertAlmostEqual(values["Field C"], 6.0)
        self.assertAlmostEqual(values["Field E"], 6.2)
        self.assertIsNone(values["Field D"])

    def test_columns_of_the_same_field_have_their_own_totals(self):
        manager = MockSameFieldSummaryTableManager()
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual([field.value for field in fields[1:]], [6, 12])

    def test_label_in_the_first_column_not_summed(self):
        manager = MockSummaryRowTableManager()
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[0].display_value, "Sum")
        self.assertEqual([field.display_value for field in fields[5:]], ["", ""])

    @override_settings(LANGUAGE_CODE="de")
    def test_german_label(self):
        manager = MockSummaryRowTableManager()
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[0].display_value, "Summe")

    def test_sums_all_rows_not_only_the_page(self):
        manager = MockLongSummaryRowTableManager({"current_paginate_by": 10})
        manager.get_table()
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[1].value, sum(range(10000)))

    def test_is_rendered_as_table_footer(self):
        html = MockSummaryRowTableManager().to_html()

        footer = BeautifulSoup(html, "html.parser").find("tfoot")
        self.assertIsNotNone(footer)
        self.assertEqual(len(footer.find_all("td")), 7)
        self.assertEqual(footer.find("td").get_text(strip=True), "Sum")

    def test_is_rendered_in_the_pdf(self):
        html = MockSummaryRowTableManager().to_pdf_html()

        footer = BeautifulSoup(html, "html.parser").find("tfoot")
        # Without the link column, as the rows of the PDF
        self.assertEqual(len(footer.find_all("td")), 6)

    def test_no_summary_row_by_default(self):
        html = MockMontrekTableManager().to_html()

        self.assertIsNone(BeautifulSoup(html, "html.parser").find("tfoot"))


class TestSummaryRowConfig(TestCase):
    def manager(self, **config):
        manager = MockSummaryRowTableManager()
        manager.summary_row_config = SummaryRowConfig(**config)
        return manager

    def test_excluded_columns_stay_empty(self):
        manager = self.manager(exclude_attrs=("field_b",))
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual((fields[1].display_value, fields[1].value), ("", None))
        self.assertAlmostEqual(fields[2].value, 6.0)

    def test_label_in_the_given_column(self):
        manager = self.manager(label_attr="field_d")
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[0].display_value, "")
        self.assertEqual(fields[3].display_value, "Sum")


class TestLargeTable(TestCase):
    def test_large_table_cannot_show_a_summary_row(self):
        with self.assertRaises(ImproperlyConfigured):

            class LargeSummaryTableManager(MockSummaryRowTableManager):
                is_large = True


class TestSummaryRowOfQuerysets(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        for name, count in (("a", 1), ("b", 2), ("c", 4)):
            me_factories.SatTSC3Factory(field_tsc3_str=name, field_tsc3_int=count)
        me_factories.SatTSC3Factory(field_tsc3_str="empty", field_tsc3_int=None)

    def test_sums_in_one_query(self):
        manager = HubCSummaryTableManager({"user_id": self.user.id})
        with CaptureQueriesContext(connection) as queries:
            fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(
            cells(fields),
            [
                ("Name", "Sum", None),
                ("Count", "7", 7),
                # Shares are not added up
                ("Share", "", None),
            ],
        )
        self.assertEqual(len(queries), 1)
        self.assertIn("SUM(", queries[0]["sql"])

    def test_sums_computed_values_in_python(self):
        manager = HubCComputedSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[1].value, 14)

    def test_columns_of_the_same_field_in_sql_and_python(self):
        manager = HubCSameFieldSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual([field.value for field in fields[1:]], [7, 14])

    def test_integers_of_a_float_column_sum_as_shown(self):
        for _ in range(2):
            me_factories.SatTSC2Factory(field_tsc2_float=1.8)
        manager = HubCFloatColumnSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        # Each row shows 1, so the column sums to 2, not to int(3.6)
        self.assertEqual(fields[1].value, 2)
        self.assertAlmostEqual(fields[2].value, 3.6)

    def test_repository_sums_only_numeric_columns(self):
        queryset = HubCRepository({}).receive()

        self.assertEqual(
            HubCRepository.get_column_sums(
                queryset, ["field_tsc3_int", "field_tsc3_str", "no_such_field"]
            ),
            {"field_tsc3_int": 7},
        )


class TestSummaryRowOfViewModels(TestCase):
    def test_sums_the_columns_of_the_view_model(self):
        user = MontrekUserFactory()
        repository = HubARepository({"user_id": user.id})
        for name, count, amount in (("a", 1, 1.5), ("b", 2, 2.5)):
            repository.create_by_dict(
                {
                    "field_a1_str": name,
                    "field_a1_int": count,
                    "field_a2_str": name,
                    "field_a2_float": amount,
                }
            )
        manager = HubASummaryTableManager({"user_id": user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual([field.value for field in fields[1:]], [3, 4.0])


class TestSummaryRowOfDataFrames(TestCase):
    def test_sums_the_rows_of_the_data_frame(self):
        df = pd.DataFrame(
            {
                "field_a": ["a", "b"],
                "field_b": [1, 2],
                "field_c": [1.5, None],
                "field_d": [None, None],
                "field_e": [10.0, 20.0],
                "Link Text": ["a", "b"],
            }
        )
        manager = MockSummaryRowDataFrameTableManager(
            {"df_data": df.to_dict(orient="records")}
        )
        fields = manager.get_summary_fields(manager.table_elements)

        values = {field.name: field.value for field in fields}
        self.assertEqual(values["Field B"], 3)
        self.assertAlmostEqual(values["Field C"], 1.5)
        self.assertAlmostEqual(values["Field E"], 30.0)
