from django.test import TestCase
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.tests import mocks


class TestMontrekReportManager(TestCase):
    def test_init(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        self.assertEqual(manager.session_data, session_data)
        self.assertEqual(manager._report_elements, [])

    def test_no_collect_report_elements(self):
        manager = mocks.MockNoCollectReportElements(session_data={})
        self.assertRaises(NotImplementedError, manager.collect_report_elements)

    def test_append_report_element(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        self.assertEqual(manager.report_elements, [report_element])

    def test_append_report_element_list(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element([report_element, report_element])
        self.assertEqual(
            manager.report_elements,
            [
                report_element,
                report_element,
                report_element,
            ],
        )

    def test_generate_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element(report_element)
        self.assertEqual(manager.generate_report(), "htmllatexhtmllatex")

    def test_cleanup_report_elements(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.cleanup_report_elements()
        self.assertEqual(manager.report_elements, [])

    def test_cleanup_after_to_html(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.to_html()
        self.assertEqual(manager.report_elements, [])

    def test_cleanup_after_to_latex(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.to_latex()
        self.assertEqual(manager.report_elements, [])

    def test_failing_report_generation(self):
        session_data = {}
        manager = mocks.MockMontrekReportManagerError(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        test_html = manager.to_html()
        self.assertEqual(
            test_html,
            '<div class="alert alert-danger"><strong>Error during report generation: This fails!</strong></div>',
        )


class TestComprehensiveReport(TestCase):
    def test_generate_report_and_compile(self):
        session_data = {}
        manager = mocks.MockComprehensiveReportManager(session_data=session_data)
        self.assertEqual(manager.document_title, "Mock Comprehensive Report")
        report_manager = LatexReportManager(manager)
        pdf_path = report_manager.compile_report()
        self.assertIn("document.pdf", pdf_path)
