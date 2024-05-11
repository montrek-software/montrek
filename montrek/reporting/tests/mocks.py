from reporting.managers.montrek_report_manager import (
    MontrekReportManager,
)
from reporting.managers.latex_report_manager import LatexReportManager


class MockMontrekReportManager(MontrekReportManager):
    document_title = "Mock Report"

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
