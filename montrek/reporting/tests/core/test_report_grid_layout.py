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
            '<div class="row"><div class="col-lg-6"><p>One</p></div><div class="col-lg-6"><p>Two</p></div></div><div class="row"><div class="col-lg-6"><p>Three</p></div><div class="col-lg-6"><p>Four</p></div></div>',
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
        self.assertEqual(
            html,
            '<div class="row"><div class="col-lg-6"><p>One</p></div><div class="col-lg-6"><p>Two</p></div></div><div class="row"><div class="col-lg-6"><div class="row"><div class="col-lg-12">Nested Two</div></div></div><div class="col-lg-6"><p>Four</p></div></div>',
        )
