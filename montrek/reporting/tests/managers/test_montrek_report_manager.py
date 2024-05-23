from django.test import TestCase

from reporting.tests import mocks


class TestMontrekReportManager(TestCase):
    def test_init(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        assert manager.session_data == session_data
        assert manager._report_elements == []

    def test_append_report_element(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        assert manager.report_elements == [report_element]

    def test_append_report_element_list(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element([report_element, report_element])
        assert manager.report_elements == [
            report_element,
            report_element,
            report_element,
        ]

    def test_generate_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element(report_element)
        assert manager.generate_report() == "htmllatexhtmllatex"
