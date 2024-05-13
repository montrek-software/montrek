from django.test import TestCase
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
        self.assertEqual(
            html,
            '<div><table id="noStyleTable"><tr><td><p>One</p></td><td><p>Two</p></td></tr><tr><td><p>Three</p></td><td><p>Four</p></td></tr></table></div>',
        )

    def test_report_grid_layout__latex(self):
        latex = self.grid.to_latex()
        self.assertEqual(
            latex.replace("\n", ""),
            r"\begin{table}[H]\begin{tabular}{ >{\raggedright\arraybackslash}p{ 0.48500\textwidth}>{\raggedleft\arraybackslash}p{ 0.48500\textwidth} }\begin{justify}One\end{justify} & \begin{justify}Two\end{justify} \\\begin{justify}Three\end{justify} & \begin{justify}Four\end{justify} \\\end{tabular}\end{table}",
        )

    def test_nested_grids(self):
        nested_grid = ReportGridLayout(1, 1)
        nested_grid.add_report_grid_element(ReportingText("Nested One"), 0, 0)
        nested_grid.add_report_grid_element(ReportingText("Nested Two"), 0, 0)
        self.grid.add_report_grid_element(nested_grid, 1, 0)
        html = self.grid.to_html()
        self.assertTrue(
            '<table id="noStyleTable"><tr><td>Nested Two</td></tr></table>' in html
        )
