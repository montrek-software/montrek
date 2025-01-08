from reporting.managers.montrek_report_manager import (
    MontrekReportManager,
)
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.core import reporting_text


class MockNoCollectReportElements(MontrekReportManager):
    pass


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


class MockComprehensiveReportManager(MontrekReportManager):
    document_title = "Mock Comprehensive Report"

    def collect_report_elements(self):
        self.append_report_element(reporting_text.ReportingHeader1("Hallo"))
