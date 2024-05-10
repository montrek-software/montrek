from django.test import TestCase
from reporting.core.reporting_grid_layout import ReportGridLayout
from reporting.core.reporting_text import ReportingParagraph


class TestReportGridLayout(TestCase):
    def test_report_grid_layout(self):
        grid = ReportGridLayout()
        grid.add_report_grid_element(ReportingParagraph("One"), 0, 0)
        grid.add_report_grid_element(ReportingParagraph("Two"), 0, 1)
        grid.add_report_grid_element(ReportingParagraph("Three"), 1, 0)
        grid.add_report_grid_element(ReportingParagraph("Four"), 1, 1)

        html = grid.to_html()
        self.assertEqual(
            html,
            "<div><table><tr><td>One</td><td>Two</td></tr><tr><td>Three</td><td>Four</td></tr></table>",
        )
