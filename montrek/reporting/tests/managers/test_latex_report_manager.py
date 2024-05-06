from django.test import TestCase
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.tests import mocks


class TestLatexReportManager(TestCase):
    def test_generate_report_no_template(self):
        manager = mocks.MockMontrekReportManager(session_data={})
        latex_manager = mocks.MockLatexReportManagerNoTemplate(manager)
        self.assertRaises(FileNotFoundError, latex_manager.generate_report)

    def test_generate_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.append_report_element(mocks.MockReportElement())
        latex_manager = LatexReportManager(manager)
        self.assertIn("latexlatex", latex_manager.generate_report())
        report = manager.generate_report()

    def test_compile_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.append_report_element(mocks.MockReportElement())
        latex_manager = LatexReportManager(manager)
        outpath = latex_manager.compile_report()
        self.assertIn("document.pdf", outpath)
