import io

import pandas as pd
from bs4 import BeautifulSoup
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from openpyxl import load_workbook

from reporting.core.table_converter import LatexTableConverter
from reporting.dataclasses import table_elements as te
from reporting.dataclasses.summary_row_config import SummaryRowConfig
from reporting.tests.mocks import (
    MockEmptyRepository,
    MockLongSummaryRowTableManager,
    MockMontrekTableManager,
    MockSummaryRowDataFrameTableManager,
    MockSummaryRowTableManager,
)


class DoubledIntTableElement(te.IntTableElement):
    def get_value(self, obj):
        value = super().get_value(obj)
        return value * 2 if isinstance(value, int) else value


class MockSameFieldSummaryTableManager(MockSummaryRowTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_a"),
            te.IntTableElement(name="Count", attr="field_b"),
            DoubledIntTableElement(name="Doubled", attr="field_b"),
        )


class MockRowCurrencySummaryTableManager(MockSummaryRowDataFrameTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_a"),
            te.MoneyTableElement(
                name="Amount", attr="field_e", ccy_symbol_field="ccy_symbol"
            ),
        )


class MockLinkFirstSummaryTableManager(MockSummaryRowTableManager):
    @property
    def table_elements(self):
        return (
            te.LinkTableElement(
                name="Details", url="home", kwargs={}, hover_text="Details", icon="eye"
            ),
            te.StringTableElement(name="Name", attr="field_a"),
            te.IntTableElement(name="Count", attr="field_b"),
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
        self.assertRaises(
            ImproperlyConfigured,
            type,
            "LargeSummaryTableManager",
            (MockSummaryRowTableManager,),
            {"is_large": True},
        )


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


class TestSummaryRowOfRowCurrencies(TestCase):
    """The total of rows in different currencies is in none of them."""

    def setUp(self):
        df = pd.DataFrame(
            {
                "field_a": ["a", "b"],
                "field_e": [10.0, 5.0],
                "ccy_symbol": ["€", "$"],
            }
        )
        self.manager = MockRowCurrencySummaryTableManager(
            {"df_data": df.to_dict(orient="records")}
        )

    def test_html_total_has_no_symbol(self):
        fields = self.manager.get_summary_fields(self.manager.table_elements)

        self.assertEqual(fields[1].display_value.strip(), "15.00")

    def test_latex_rows_have_their_symbol_and_the_total_none(self):
        latex = self.manager.to_latex()

        self.assertIn("10.00€\\\\\n", latex)
        self.assertIn("5.00\\$\\\\\n", latex)
        self.assertIn("\\bfseries \\color{textdark} 15.00\\\\\n", latex)


class TestSummaryRowInExports(TestCase):
    def excel_sheet(self, manager):
        workbook = load_workbook(manager.to_excel(io.BytesIO()))
        return workbook.active

    def test_excel_sheet_ends_with_the_summary_row(self):
        sheet = self.excel_sheet(MockSummaryRowTableManager())

        self.assertEqual(sheet.max_row, 5)
        last_row = [cell.value for cell in sheet[5]]
        self.assertEqual(last_row[:3], ["Sum", 6, 6.0])
        self.assertAlmostEqual(last_row[4], 6.2)
        self.assertEqual(last_row[3], None)

    def test_excel_summary_row_is_bold_under_a_line(self):
        sheet = self.excel_sheet(MockSummaryRowTableManager())

        self.assertTrue(sheet["B5"].font.bold)
        self.assertEqual(sheet["B5"].border.top.style, "medium")
        self.assertFalse(sheet["B4"].font.bold)

    def test_excel_sheet_of_a_data_frame_table(self):
        df = pd.DataFrame(
            {
                "field_a": ["a", "b"],
                "field_b": [1, 2],
                "field_c": [1.5, 2.5],
                "field_d": [None, None],
                "field_e": [10.0, 20.0],
                "Link Text": ["a", "b"],
            }
        )
        manager = MockSummaryRowDataFrameTableManager(
            {"df_data": df.to_dict(orient="records")}
        )
        sheet = self.excel_sheet(manager)

        header = [cell.value for cell in sheet[1]]
        last_row = dict(zip(header, [cell.value for cell in sheet[4]], strict=True))
        self.assertEqual(last_row["Field_A"], "Sum")
        self.assertEqual(last_row["Field B"], 3)
        self.assertEqual(last_row["Field E"], 30)

    def test_excel_totals_are_numbers(self):
        manager = MockSummaryRowTableManager()
        frame = manager.get_excel_frame()

        self.assertIsInstance(frame.iloc[-1]["Field E"], float)

    def test_csv_has_no_summary_row(self):
        csv = MockSummaryRowTableManager().to_csv(io.StringIO()).getvalue()

        self.assertEqual(len(csv.splitlines()), 4)
        self.assertNotIn("Sum", csv)

    def test_latex_table_ends_with_the_summary_row(self):
        latex = MockSummaryRowTableManager().to_latex()

        self.assertEqual(latex.count("\\bfseries Sum &"), 1)
        # Set off from the rows by the rule in the primary colour
        summary = latex.rsplit("\\arrayrulecolor{primary}\\hline", 1)[1]
        self.assertTrue(
            summary.removeprefix("\\arrayrulecolor{bordercolor}\n").startswith(
                "\\bfseries Sum &"
            )
        )
        self.assertIn("\\end{tabularx}", summary)

    def test_latex_summary_row_only_after_the_last_page(self):
        class TwoRowPageManager(MockSummaryRowTableManager):
            latex_rows_per_page = 2

        latex = TwoRowPageManager().to_latex()

        self.assertEqual(latex.count("\\bfseries Sum &"), 1)
        self.assertGreater(latex.index("\\bfseries Sum"), latex.index("\\newpage"))

    def test_long_latex_table_ends_with_the_summary_row(self):
        class LongTableManager(MockSummaryRowTableManager):
            latex_long_table = True

        latex = LongTableManager().to_latex()

        self.assertEqual(latex.count("\\bfseries Sum &"), 1)
        self.assertLess(latex.index("\\bfseries Sum"), latex.index("\\end{longtable}"))

    def test_latex_without_rows_has_no_summary_row(self):
        class EmptyManager(MockSummaryRowTableManager):
            repository_class = MockEmptyRepository

        self.assertNotIn("\\bfseries Sum", EmptyManager().to_latex())

    def test_latex_label_after_a_leading_link_column(self):
        latex = MockLinkFirstSummaryTableManager().to_latex()

        self.assertIn("\\bfseries Sum &", latex)

    def test_excel_label_after_a_leading_link_column(self):
        sheet = self.excel_sheet(MockLinkFirstSummaryTableManager())

        self.assertEqual([cell.value for cell in sheet[sheet.max_row]], ["Sum", 6])

    def test_html_label_in_the_leading_link_column(self):
        manager = MockLinkFirstSummaryTableManager()
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[0].display_value, "Sum")

    def test_latex_width_of_a_currency_total_includes_the_symbol(self):
        element = te.EuroTableElement(name="Amount", attr="amount")

        self.assertEqual(element.get_sum_value_len(1000), len("1,000.00€"))

    def test_latex_column_fits_the_total(self):
        manager = MockLongSummaryRowTableManager()
        converter = LatexTableConverter(
            manager.table_title,
            manager.table_elements,
            manager.get_full_table(),
            summary_cells=[(" &", 0), ("\\bfseries 49,995,000 &", 10)],
        )
        converter.get_table_str()

        self.assertEqual(max(converter.column_sizer[1]), 10)
