import re

from bs4 import BeautifulSoup
from django.test import TestCase
from reporting.tests.mocks import MockMontrekDetailsManager


class TestMontrekDetailsManager(TestCase):
    @staticmethod
    def _table_to_map(table_tag):
        """
        Build a dict mapping <th> text -> <td> Tag for easy lookup.
        """
        out = {}
        for tr in table_tag.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td:
                out[th.get_text(strip=True)] = td
        return out

    def test_to_html(self):
        html = MockMontrekDetailsManager().to_html()
        soup = BeautifulSoup(html, "html.parser")  # use "lxml" if you have it installed

        # overall layout
        cols = soup.select("div.row > div.col-md-6")
        self.assertEqual(len(cols), 2)

        tables = soup.select("table.table.table-bordered.table-hover.table-responsive")
        self.assertEqual(len(tables), 2)

        left_map = self._table_to_map(tables[0])
        right_map = self._table_to_map(tables[1])

        # --- Left table checks ---
        self.assertIn("Field A", left_map)
        self.assertIn("Field B", left_map)
        self.assertIn("Field C", left_map)
        self.assertIn("Field D", left_map)

        self.assertEqual(left_map["Field A"].get_text(strip=True), "a")
        self.assertEqual(left_map["Field B"].get_text(strip=True), "1")
        self.assertEqual(left_map["Field C"].get_text(strip=True), "1.000")
        self.assertIn("2024-07-13", left_map["Field D"].get_text(strip=True))

        # style checks (don’t overfit exact order/spacing)
        style_b = left_map["Field B"].get("style", "")
        self.assertIn("text-align:right", style_b)
        self.assertIn("#002F6C", style_b)

        style_c = left_map["Field C"].get("style", "")
        self.assertIn("text-align:right", style_c)
        self.assertIn("#002F6C", style_c)

        # --- Right table checks ---
        self.assertIn("Field E", right_map)
        self.assertTrue(right_map["Field E"].get_text(strip=True).endswith("€"))
        style_e = right_map["Field E"].get("style", "")
        self.assertIn("text-align:right", style_e)

        # Link cell with icon
        self.assertIn("Link", right_map)
        link_a = right_map["Link"].find("a", id="id__home")
        self.assertIsNotNone(link_a)
        self.assertEqual(link_a.get("href"), "/home")
        self.assertEqual(link_a.get("title"), "Link")
        self.assertIsNotNone(link_a.find("span", class_="glyphicon"))

        # Link Text cell with anchor text
        self.assertIn("Link Text", right_map)
        link_text_a = right_map["Link Text"].find("a", id="id__home")
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
            r"\\cellcolor{blue}\\color{white}\\textbf{Link}\s*&\s*\\cellcolor{lightblue}\s*\\color{black}\s*<span class=\"glyphicon glyphicon-icon\"></span>\s*\\\\",
        )
        self.assertRegexPresent(
            latex,
            r"\\cellcolor{blue}\\color{white}\\textbf{Link Text}\s*&\s*\\color{black}\s*a\s*\\\\",
        )

        # Each row separated by \hline (we expect 8: one after each row)
        self.assertGreaterEqual(len(re.findall(r"\\hline", latex)), 8)

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
