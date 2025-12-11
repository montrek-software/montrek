import re

from bs4 import BeautifulSoup
from django.test import TestCase
from reporting.tests.mocks import (
    MockMontrekDetailsManager,
    MockMontrekDetailsManager5Cols,
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
        style_e = field_e_td.get("style", "")
        self.assertIn("color", style_e)
        self.assertIn("#002F6C", style_e)

        # Link cell with icon
        link_td = cell_map["Link"]
        link_a = link_td.find("a", id="id__home")
        self.assertIsNotNone(link_a)
        self.assertEqual(link_a.get("href"), "/home")
        self.assertEqual(link_a.get("title"), "Link")
        self.assertIsNotNone(link_a.find("span", class_="bi"))

        # Link Text cell with anchor text
        link_text_td = cell_map["Link Text"]
        link_text_a = link_text_td.find("a", id="id__home")
        self.assertIsNotNone(link_text_a)
        self.assertEqual(link_text_a.get("href"), "/home")
        self.assertEqual(link_text_a.get("title"), "Link Text")
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
        self.assertIn(r"\arrayrulecolor{lightgrey}", latex)
        self.assertIn(r"\setlength{\tabcolsep}{2pt}", latex)
        self.assertIn(r"\renewcommand{\arraystretch}{1.0}", latex)

        # --- Left table rows ---
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Field A}\s*&\s*\\color{black}\s*a\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Field B}\s*&\s*\\cellcolor{lightblue}\s*\\color{darkblue}\s*1\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Field C}\s*&\s*\\color{darkblue}\s*1\.000\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Field D}\s*&\s*\\cellcolor{lightblue}\s*\\color{black}\s*2024-07-13 00:00:00\s*\\\\",
        )

        # --- Right table rows ---
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Field E}\s*&\s*\\color{darkblue}\s*1\.00€\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Link}\s*&\s*\\cellcolor{lightblue}\s*\\color{black}\s*\\twemoji{pencil}\s*\\+",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Link Text}\s*&\s*\\color{black}\s*a\s*\\\\",
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
