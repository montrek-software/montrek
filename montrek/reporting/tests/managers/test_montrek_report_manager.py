from django.test import TestCase
from reporting.managers.montrek_report_manager import MontrekReportManager


class MockMontrekReportManager(MontrekReportManager):
    pass


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
