import pandas as pd

from reporting.constants import ReportingPlotType
from reporting.core import reporting_text
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_grid_layout import ReportGridLayout
from reporting.core.reporting_plots import ReportingPlot
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import (
    MontrekReportManager,
)


class MockNoCollectReportElements(MontrekReportManager):
    pass


class MockMontrekReportManager(MontrekReportManager):
    document_title = "Mock Report"

    def collect_report_elements(self):
        pass

    def generate_report(self) -> str:
        report = ""
        for report_element in self.report_elements:
            report += report_element.to_html()
            report += report_element.to_latex()
        return report


class MockReportElement:
    def to_html(self):
        return "html"

    def to_latex(self):
        return "latex"


class MockLatexReportManagerNoTemplate(LatexReportManager):
    latex_template = "no_template.tex"


class MockComprehensiveReportManager(MontrekReportManager):
    document_title = "Mock Comprehensive Report"

    def collect_report_elements(self):
        self.append_report_element(reporting_text.ReportingHeader1("Hallo"))
        self.append_report_element(self.grid())

    def grid(self):
        grid = ReportGridLayout(2, 2)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("One"), 0, 0)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("Two"), 0, 1)
        grid.add_report_grid_element(self.plot(grid.width), 1, 0)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("Four"), 1, 1)
        return grid

    def plot(self, width):
        test_df = pd.DataFrame(
            {
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 25, 15, 30],
            },
        )
        reporting_data = ReportingData(
            data_df=test_df,
            x_axis_column="Category",
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.PIE],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot(width=width)
        reporting_plot.generate(reporting_data)
        return reporting_plot
