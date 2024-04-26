from django.test import TestCase
from reporting.managers.montrek_report_manager import (
    MontrekReportManager,
    LatexReportManager,
)


class MockMontrekReportManager(MontrekReportManager):
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


class TestMontrekReportManager(TestCase):
    def test_init(self):
        session_data = {}
        manager = MockMontrekReportManager(session_data=session_data)
        assert manager.session_data == session_data
        assert manager._report_elements == []

    def test_append_report_element(self):
        session_data = {}
        manager = MockMontrekReportManager(session_data=session_data)
        report_element = MockReportElement()
        manager.append_report_element(report_element)
        assert manager.report_elements == [report_element]

    def test_generate_report(self):
        session_data = {}
        manager = MockMontrekReportManager(session_data=session_data)
        report_element = MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element(report_element)
        assert manager.generate_report() == "htmllatexhtmllatex"


class MockLatexReportManagerNoTemplate(LatexReportManager):
    latex_template = "no_template.tex"


class TestLatexReportManager(TestCase):
    def test_generate_report(self):
        session_data = {}
        manager = MockLatexReportManagerNoTemplate(session_data=session_data)
        self.assertRaises(FileNotFoundError, manager.generate_report)
