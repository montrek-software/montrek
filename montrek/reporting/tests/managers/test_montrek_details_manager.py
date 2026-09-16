import re
from io import BytesIO

from bs4 import BeautifulSoup
from django.test import TestCase
from openpyxl import load_workbook
from reporting.dataclasses import table_elements as te
from reporting.managers.excel_export import write_excel_workbook
from reporting.tests.mocks import (
    MockMontrekDetailsManager,
    MockMontrekDetailsManager5Cols,
    MockMontrekTableManager,
)


class TestMontrekDetailsManager(TestCase):
    @staticmethod
    def _table_to_map(table):
        """
        Build a dict mapping <th> text -> <td> Tag for easy lookup.
        """
        mapping = {}
        for row in table.find_all("tr"):
            headers = row.find_all("th")
            cells = row.find_all("td")
            # pair headers and cells positionally in this row
            for i, th in enumerate(headers):
                if i < len(cells):
                    key = " ".join(th.get_text(strip=True).split())
                    mapping[key] = cells[i]
        return mapping

    def test_to_html(self):
        html = MockMontrekDetailsManager().to_html()
        soup = BeautifulSoup(html, "html.parser")

        # single table now
        tables = soup.select(
            "table.table.table-custom-striped.table-bordered.table-hover.table-responsive"
        )
        self.assertEqual(len(tables), 1)
        table = tables[0]

        cell_map = self._table_to_map(table)

        # --- presence checks ---
        for label in [
            "Field A",
            "Field B",
            "Field C",
            "Field D",
            "Field E",
            "Link",
            "Link Text",
        ]:
            self.assertIn(label, cell_map)

        # --- value checks ---
        self.assertEqual(cell_map["Field A"].get_text(strip=True), "a")
        self.assertEqual(cell_map["Field B"].get_text(strip=True), "1")
        self.assertEqual(cell_map["Field C"].get_text(strip=True), "1.000")
        self.assertIn("2024-07-13", cell_map["Field D"].get_text(strip=True))

        # Field E with currency and style
        field_e_td = cell_map["Field E"]
        self.assertTrue(field_e_td.get_text(strip=True).endswith("€"))
        # Non-negative numbers inherit the table text color (no inline style)
        style_e = field_e_td.get("style", "")
        self.assertNotIn("color", style_e)

        # Link cell with icon
        link_td = cell_map["Link"]
        self.assertEqual(link_td.get("data-bs-title"), "Link")
        self.assertEqual(link_td.get("data-bs-toggle"), "tooltip")
        link_a = link_td.find("a", id="id__home")
        self.assertIsNotNone(link_a)
        self.assertEqual(link_a.get("href"), "/home")
        self.assertIsNotNone(link_a.find("span", class_="bi"))

        # Link Text cell with anchor text
        link_text_td = cell_map["Link Text"]
        self.assertEqual(link_text_td.get("data-bs-title"), "Link Text")
        link_text_a = link_text_td.find("a", id="id__home")
        self.assertIsNotNone(link_text_a)
        self.assertEqual(link_text_a.get("href"), "/home")
        self.assertEqual(link_text_a.get_text(strip=True), "a")

    def assertRegexPresent(self, text: str, pattern: str, msg: str = ""):
        """Helper that shows the missing pattern nicely on failure."""
        if not re.search(pattern, text, flags=re.DOTALL):
            self.fail(msg or f"Pattern not found:\n{pattern}\n\nin text:\n{text}")

    def test_to_latex(self):
        latex = MockMontrekDetailsManager().to_latex()
        # --- High-level structure ---
        # Two minipages side-by-side
        self.assertEqual(
            len(re.findall(r"\\begin\{minipage\}\[t\]\{0\.49\\textwidth\}", latex)), 2
        )
        self.assertEqual(len(re.findall(r"\\end\{minipage\}", latex)), 2)

        # Each minipage contains a table
        self.assertEqual(len(re.findall(r"\\begin\{table\}\[H\]", latex)), 2)
        self.assertEqual(len(re.findall(r"\\end\{table\}", latex)), 2)

        # Common table preamble bits
        self.assertIn(r"\arrayrulecolor{bordercolor}", latex)
        # Font size, padding and row height are the template's job
        # (\montrektablesetup), not the converter's.
        self.assertIn(r"\montrektablesetup", latex)

        # --- Left table rows ---
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Field A}\s*&\s*\\color{textdark}\s*a\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Field B}\s*&\s*\\color{textdark}\s*1\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Field C}\s*&\s*\\color{textdark}\s*1\.000\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Field D}\s*&\s*\\color{textdark}\s*2024-07-13 00:00:00\s*\\\\",
        )

        # --- Right table rows ---
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Field E}\s*&\s*\\color{textdark}\s*1\.00€\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Link}\s*&\s*\\color{textdark}\s*\\twemoji{pencil}\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\montrekdetailsheadcell{Link Text}\s*&\s*\\color{textdark}\s*a\s*\\\\",
        )

        # Each row separated by \hline (we expect 8: one after each row)
        self.assertGreaterEqual(len(re.findall(r"\\hline", latex)), 8)

    def test_montrek_details_column_width(self):
        context_data = MockMontrekDetailsManager({}).get_context_data()
        self.assertEqual(context_data["col_range"], range(2))
        self.assertEqual(context_data["col_widths_head"], 15.0)
        self.assertEqual(context_data["col_widths_body"], 35.0)
        context_data = MockMontrekDetailsManager5Cols({}).get_context_data()
        self.assertEqual(context_data["col_range"], range(5))
        self.assertEqual(context_data["col_widths_head"], 10.0)
        self.assertEqual(context_data["col_widths_body"], 10.0)

    def test_to_json(self):
        json = MockMontrekDetailsManager().to_json()
        self.assertEqual(
            json,
            {
                "field_a": "a",
                "field_b": 1,
                "field_c": 1.0,
                "field_d": "2024-07-13T00:00:00",
                "field_e": 1.0,
            },
        )


class TestMontrekDetailsManagerExcel(TestCase):
    """The details sheet mirrors the HTML block: label/value pairs laid out
    down the columns, a pair per column of the grid."""

    def get_sheet(self, manager_class=MockMontrekDetailsManager):
        output = manager_class().to_excel(BytesIO())
        return load_workbook(BytesIO(output.getvalue())).active

    def get_cells(self, manager_class=MockMontrekDetailsManager):
        return [
            [cell.value for cell in row] for row in self.get_sheet(manager_class).rows
        ]

    def test_columns_alternate_label_and_value(self):
        """Label, value, label, value - a pair per column of the grid."""
        rows = self.get_cells()

        self.assertEqual(
            [[row[0], row[2]] for row in rows],
            [
                ["Field A", "Field D"],
                ["Field B", "Field E"],
                ["Field C", "Link Text"],
            ],
        )
        self.assertEqual([row[1] for row in rows], ["a", 1, 1.0])

    def test_pairs_per_row_follow_table_cols(self):
        """Two grid columns means two label/value pairs, so four cells."""
        self.assertTrue(all(len(row) == 4 for row in self.get_cells()))

        wide_rows = self.get_cells(MockMontrekDetailsManager5Cols)

        self.assertTrue(all(len(row) == 10 for row in wide_rows))

    def test_labels_follow_the_grids_reading_order(self):
        """Down the columns, as the HTML block reads.

        Not a cell-for-cell copy of that block: the icon link is dropped
        before the layout, so six fields fall into three rows where the seven
        on screen fall into four. What carries over is the reading order over
        the fields that can be exported.
        """
        manager = MockMontrekDetailsManager()
        expected = [
            element.name
            for grid_row in manager.arrange_in_grid(manager.excel_table_elements)
            for element in grid_row
        ]
        excel_labels = [
            cell
            for row in self.get_cells()
            for index, cell in enumerate(row)
            if index % 2 == 0 and cell is not None
        ]

        self.assertEqual(excel_labels, expected)

    def test_icon_links_are_left_out_but_link_text_is_kept(self):
        """An icon link carries no value and nothing to click in a
        spreadsheet; a link text column carries its text."""
        labels = [cell for row in self.get_cells() for cell in row]

        self.assertNotIn("Link", labels)
        self.assertIn("Link Text", labels)

    def test_values_keep_their_own_number_format(self):
        """The format follows the field, not the column.

        Field D and Field E share the second value column and want different
        formats, which a per-column mapping could not give them.
        """
        sheet = self.get_sheet()
        formats = {}
        for row in sheet.rows:
            for index, cell in enumerate(row):
                if index % 2 == 0 and cell.value is not None:
                    formats[cell.value] = row[index + 1].number_format

        self.assertEqual(formats["Field E"], "#,##0.00")
        self.assertEqual(formats["Field C"], "#,##0.000")
        self.assertEqual(formats["Field A"], "General")
        # A datetime brings its own format from openpyxl, which is only
        # reachable because the value is written as a datetime rather than as
        # its rendered text.
        self.assertEqual(formats["Field D"], "YYYY-MM-DD HH:MM:SS")

    def test_labels_are_styled_like_the_html_headers(self):
        sheet = self.get_sheet()

        self.assertTrue(sheet["A1"].font.bold)
        self.assertFalse(sheet["B1"].font.bold)

    def test_a_details_block_and_a_table_share_one_workbook(self):
        """The point of the sheet mechanic: a download can put the details
        block and a table side by side."""
        output = write_excel_workbook(
            BytesIO(),
            {
                "Details": MockMontrekDetailsManager(),
                "Table": MockMontrekTableManager(),
            },
        )
        workbook = load_workbook(BytesIO(output.getvalue()))

        self.assertEqual(workbook.sheetnames, ["Details", "Table"])
        # The table sheet keeps its header row; the details sheet has none.
        self.assertTrue(workbook["Table"]["A1"].font.bold)
        self.assertEqual(workbook["Details"]["A1"].value, "Field A")


class FormulaTextTableElement(te.StringTableElement):
    """A field whose stored text looks like a spreadsheet formula."""

    def get_value(self, _obj):
        return "=1+1"


class MockFormulaDetailsManager(MockMontrekDetailsManager):
    @property
    def table_elements(self):
        return (FormulaTextTableElement(attr="field_a", name="Field A"),)


class MockFormulaTableManager(MockMontrekTableManager):
    @property
    def table_elements(self):
        return (FormulaTextTableElement(attr="field_a", name="Field A"),)


class TestExcelFormulaText(TestCase):
    """Exported fields carry text people typed, and openpyxl types a string
    starting with "=" as a formula - so it has to be written back as text, or
    opening an export runs whatever was entered."""

    def get_value_cell(self, manager, column: str):
        output = manager.to_excel(BytesIO())
        return load_workbook(BytesIO(output.getvalue())).active[column]

    def test_details_export_writes_formula_text_as_text(self):
        cell = self.get_value_cell(MockFormulaDetailsManager(), "B1")

        self.assertEqual(cell.data_type, "s")
        self.assertEqual(cell.value, "=1+1")

    def test_table_export_writes_formula_text_as_text(self):
        cell = self.get_value_cell(MockFormulaTableManager(), "A2")

        self.assertEqual(cell.data_type, "s")
        self.assertEqual(cell.value, "=1+1")
