from django.test import TestCase
from bs4 import BeautifulSoup
from reporting.core.reporting_grid_layout import ReportGridLayout
from reporting.core.reporting_text import ReportingParagraph, ReportingText


class TestReportGridLayout(TestCase):
    def setUp(self):
        self.grid = ReportGridLayout(2, 2)
        self.grid.add_report_grid_element(ReportingParagraph("One"), 0, 0)
        self.grid.add_report_grid_element(ReportingParagraph("Two"), 0, 1)
        self.grid.add_report_grid_element(ReportingParagraph("Three"), 1, 0)
        self.grid.add_report_grid_element(ReportingParagraph("Four"), 1, 1)

    def test_report_grid_layout__html(self):
        html = self.grid.to_html()
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.find_all("div", class_="row")
        self.assertEqual(len(rows), 2)

        expected = [
            ["One", "Two"],
            ["Three", "Four"],
        ]

        for row, expected_texts in zip(rows, expected, strict=False):
            cols = row.find_all("div", class_="col-lg-6")
            self.assertEqual(len(cols), 2)

            texts = [col.get_text(strip=True) for col in cols]
            self.assertEqual(texts, expected_texts)

    def test_report_grid_layout__latex(self):
        latex = self.grid.to_latex()
        self.assertTrue(
            latex.replace("\n", "").startswith(
                r"\begin{table}[H]\begin{tabular}{ >{\raggedright\arraybackslash}p{ 0.49000\textwidth}>{\raggedleft\arraybackslash}p{ 0.49000\textwidth} }\begin{minipage}[t]{0.49\textwidth}"
            )
        )

    def test_report_grid_layout__json(self):
        json = self.grid.to_json()
        expected_json = {
            "report_grid_elements": [
                [{"reportingparagraph": "One"}, {"reportingparagraph": "Two"}],
                [{"reportingparagraph": "Three"}, {"reportingparagraph": "Four"}],
            ]
        }
        self.assertEqual(json, expected_json)

    def test_nested_grids(self):
        nested_grid = ReportGridLayout(2, 1)
        nested_grid.add_report_grid_element(ReportingText("Nested One"), 0, 0)
        nested_grid.add_report_grid_element(ReportingText("Nested Two"), 1, 0)
        self.grid.add_report_grid_element(nested_grid, 1, 0)
        html = self.grid.to_html()
        soup = BeautifulSoup(html, "html.parser")

        # Top-level rows
        rows = soup.find_all("div", class_="row", recursive=False)
        self.assertEqual(len(rows), 2)

        # Row 1: simple texts
        row1_cols = rows[0].find_all("div", class_="col-lg-6", recursive=False)
        self.assertEqual(
            [c.get_text(strip=True) for c in row1_cols],
            ["One", "Two"],
        )

        # Row 2
        row2_cols = rows[1].find_all("div", class_="col-lg-6", recursive=False)
        self.assertEqual(len(row2_cols), 2)

        # Row 2, Col 1: nested grid
        nested_rows = row2_cols[0].find_all("div", class_="row", recursive=False)
        self.assertEqual(len(nested_rows), 2)

        nested_cols = nested_rows[0].find_all(
            "div", class_="col-lg-12", recursive=False
        )
        self.assertEqual(len(nested_cols), 1)
        self.assertEqual(nested_cols[0].get_text(strip=True), "Nested One")
        nested_cols = nested_rows[1].find_all(
            "div", class_="col-lg-12", recursive=False
        )
        self.assertEqual(len(nested_cols), 1)
        self.assertEqual(nested_cols[0].get_text(strip=True), "Nested Two")

        # Row 2, Col 2: simple text
        self.assertEqual(row2_cols[1].get_text(strip=True), "Four")

    def test_nested_grids__overlay(self):
        nested_grid = ReportGridLayout(1, 1)
        nested_grid.add_report_grid_element(ReportingText("Nested One"), 0, 0)
        nested_grid.add_report_grid_element(ReportingText("Nested Two"), 0, 0)
        self.grid.add_report_grid_element(nested_grid, 1, 0)
        html = self.grid.to_html()
        soup = BeautifulSoup(html, "html.parser")

        # Top-level rows
        rows = soup.find_all("div", class_="row", recursive=False)
        self.assertEqual(len(rows), 2)

        # Row 1: simple texts
        row1_cols = rows[0].find_all("div", class_="col-lg-6", recursive=False)
        self.assertEqual(
            [c.get_text(strip=True) for c in row1_cols],
            ["One", "Two"],
        )

        # Row 2
        row2_cols = rows[1].find_all("div", class_="col-lg-6", recursive=False)
        self.assertEqual(len(row2_cols), 2)

        # Row 2, Col 1: nested grid
        nested_rows = row2_cols[0].find_all("div", class_="row", recursive=False)
        self.assertEqual(len(nested_rows), 1)

        nested_cols = nested_rows[0].find_all(
            "div", class_="col-lg-12", recursive=False
        )
        self.assertEqual(len(nested_cols), 1)
        self.assertEqual(nested_cols[0].get_text(strip=True), "Nested Two")

        # Row 2, Col 2: simple text
        self.assertEqual(row2_cols[1].get_text(strip=True), "Four")

    def test_nested_grids__raise_error_when_no_rows_defined(self):
        nested_grid = ReportGridLayout(1, 1)
        nested_grid.add_report_grid_element(ReportingText("Nested One"), 0, 0)
        with self.assertRaises(IndexError, msg=""):
            nested_grid.add_report_grid_element(ReportingText("Nested Two"), 1, 0)
