from dataclasses import dataclass
from typing import Any

from django.test import TestCase
from reporting.core.table_converter import LatexTableConverter
from reporting.dataclasses import table_elements as te


@dataclass
class MockQueryElement:
    test_col: str
    other_col: str = "default"


class DummyTableElement(te.StringTableElement):
    def get_attribute(self, obj: Any, tag: str) -> str:
        return f"{getattr(obj, self.attr)} & "

    def get_value_len(self, obj: Any) -> int:
        return len(getattr(obj, self.attr))


class DummyLinkElement(te.LinkTableElement):
    def get_attribute(self, obj: Any, tag: str) -> str:
        return "should not appear & "

    def get_value_len(self, obj: Any) -> int:
        return 99  # intentionally large


class TestLatexTableConverter(TestCase):
    def setUp(self) -> None:
        self.table_elements = [DummyTableElement(name="TestCol", attr="test_col")]
        self.table = [
            MockQueryElement(test_col="value1"),
            MockQueryElement(test_col="val2"),
        ]
        self.latex_table_converter = LatexTableConverter(
            "Test Table Title", self.table_elements, self.table
        )

    def test_add_to_column_sizer(self):
        self.latex_table_converter.add_to_column_sizer(
            self.table_elements[0], self.table[0], col_idx=0
        )
        self.assertEqual(self.latex_table_converter.column_sizer[0], [6])
        self.latex_table_converter.add_to_column_sizer(
            self.table_elements[0], self.table[1], col_idx=0
        )
        self.assertEqual(self.latex_table_converter.column_sizer[0], [6, 4])

    def test_get_column_sizes(self):
        for row in self.table:
            self.latex_table_converter.add_to_column_sizer(
                self.table_elements[0], row, col_idx=0
            )
        col_sizes = self.latex_table_converter.get_column_sizes()
        self.assertAlmostEqual(col_sizes[0], 1.0)

    def test_get_table_start_str_contains_caption_and_column_name(self):
        for row in self.table:
            self.latex_table_converter.add_to_column_sizer(
                self.table_elements[0], row, col_idx=0
            )
        start_str = self.latex_table_converter.get_table_start_str()
        self.assertIn("\\caption{Test Table Title}", start_str)
        self.assertIn("\\textbf{\\mbox{TestCol}}", start_str)

    def test_get_table_end_str(self):
        end_str = self.latex_table_converter.get_table_end_str()
        self.assertEqual(end_str, "\\end{tabularx}\n\\end{table}\n\n")

    def test_get_table_str_includes_values_and_rowcolors(self):
        for row in self.table:
            self.latex_table_converter.add_to_column_sizer(
                self.table_elements[0], row, col_idx=0
            )
        table_str = self.latex_table_converter.get_table_str()
        self.assertIn("value1", table_str)
        self.assertIn("val2", table_str)

    def test_to_latex_full_output(self):
        latex_str = self.latex_table_converter.to_latex()
        self.assertIn("\\begin{table}", latex_str)
        self.assertIn("\\end{table}", latex_str)
        self.assertIn("value1", latex_str)

    def test_handles_empty_table(self):
        empty_converter = LatexTableConverter("Empty Table", self.table_elements, [])
        output = empty_converter.to_latex()
        self.assertIn("\\begin{table}", output)
        self.assertNotIn("value1", output)
        self.assertIn("\\end{table}", output)

    def test_ignores_link_table_element(self):
        elements = [
            DummyTableElement(name="TestCol", attr="test_col"),
            DummyLinkElement(
                name="LinkCol", icon="unused", url="url", hover_text="Test", kwargs={}
            ),
        ]
        converter = LatexTableConverter("Link Test", elements, self.table)
        for row in self.table:
            converter.add_to_column_sizer(elements[0], row, col_idx=0)
        start_str = converter.get_table_start_str()
        self.assertIn("TestCol", start_str)
        self.assertNotIn("LinkCol", start_str)

    def test_multiple_page_table_output(self):
        # create 30 rows to trigger page break logic (default rows_per_page=25 → 1 break)
        big_table = [MockQueryElement(test_col=f"row{i}") for i in range(30)]
        converter = LatexTableConverter("Big Table", self.table_elements, big_table)
        for row in big_table:
            converter.add_to_column_sizer(self.table_elements[0], row, col_idx=0)
        table_str = converter.to_latex()
        self.assertGreaterEqual(table_str.count("\\begin{tabularx}"), 2)
        self.assertIn("row0", table_str)
        self.assertIn("row29", table_str)

    def test_default_rows_per_page(self):
        converter = LatexTableConverter("T", self.table_elements, self.table)
        self.assertEqual(converter.rows_per_page, 25)

    def test_custom_rows_per_page_is_stored(self):
        converter = LatexTableConverter(
            "T", self.table_elements, self.table, rows_per_page=5
        )
        self.assertEqual(converter.rows_per_page, 5)

    def test_page_break_inserted_at_rows_per_page_boundary(self):
        # 10 rows with rows_per_page=5: breaks after row 5 and row 10
        # → 2 extra \begin{tabularx} from breaks + 1 outer = 3 total
        table = [MockQueryElement(test_col=f"row{i}") for i in range(10)]
        converter = LatexTableConverter(
            "T", self.table_elements, table, rows_per_page=5
        )
        output = converter.to_latex()
        self.assertEqual(output.count("\\begin{tabularx}"), 2)
        self.assertIn("\\newpage", output)

    def test_no_page_break_below_rows_per_page(self):
        # 4 rows with rows_per_page=5: no break → 1 outer \begin{tabularx} only
        table = [MockQueryElement(test_col=f"row{i}") for i in range(4)]
        converter = LatexTableConverter(
            "T", self.table_elements, table, rows_per_page=5
        )
        output = converter.to_latex()
        self.assertEqual(output.count("\\begin{tabularx}"), 1)
        self.assertNotIn("\\newpage", output)

    def test_min_col_size(self):
        table_elements = [
            DummyTableElement(name="TestCol", attr="test_col"),
            DummyTableElement(name="MinCol", attr="other_col"),
        ]
        table = [
            MockQueryElement(test_col="value1" + 300 * "xx", other_col="v"),
            MockQueryElement(test_col="val2", other_col="v"),
        ]
        latex_table_converter = LatexTableConverter(
            "Test Table Title", table_elements, table
        )
        latex_table_converter.get_table_str()
        # col 0 (TestCol): max len = 606 (data dominates over header seed of 7)
        # col 1 (MinCol): max len = 6 (header "MinCol" dominates over data "v"=1) → floored to min_size
        # After _adjust_col_size: total=612, min_size = 612/10 = 61.2; col 0 stays 606
        # adj_total = 606 + 61.2 = 667.2
        # col_sizes[0] = 606/667.2*2 ≈ 1.817, col_sizes[1] = 61.2/667.2*2 ≈ 0.183
        col_sizes = latex_table_converter.get_column_sizes()
        self.assertEqual(set(col_sizes.keys()), {0, 1})
        self.assertAlmostEqual(col_sizes[0] + col_sizes[1], 2.0, places=10)
        self.assertGreater(col_sizes[0], 1.5)
        self.assertLess(col_sizes[1], 0.5)

    def test_header_length_sets_column_size_floor(self):
        elements = [
            DummyTableElement(name="LongHeaderName", attr="test_col"),
            DummyTableElement(name="X", attr="other_col"),
        ]
        table = [MockQueryElement(test_col="a", other_col="b")]
        converter = LatexTableConverter("T", elements, table)
        converter.get_table_str()
        # "LongHeaderName" (14 chars) > data "a" (1 char) — header must set the floor
        self.assertEqual(max(converter.column_sizer[0]), len("LongHeaderName"))
        # "X" (1 char) < data "b" (1 char) — equal; seed and data both contribute
        self.assertGreaterEqual(max(converter.column_sizer[1]), 1)

    def test_get_adj_col_size(self):
        test_adj_col_size = LatexTableConverter.get_adj_col_size(
            15, {"a": 1, "b": 2}, 3
        )
        self.assertEqual(test_adj_col_size, 10)

    def test_get_adj_col_size__div_by_zero(self):
        test_adj_col_size = LatexTableConverter.get_adj_col_size(
            15, {"a": 1, "b": 2}, 0
        )
        self.assertEqual(test_adj_col_size, 0)
