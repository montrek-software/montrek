import os

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
        generated_report_tex = latex_manager.generate_report()
        self.assertIn("latexlatex", generated_report_tex)
        self.assertIn("Mock Report", generated_report_tex)

    def test_compile_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.append_report_element(mocks.MockReportElement())
        latex_manager = LatexReportManager(manager)
        outpath = latex_manager.compile_report()
        self.assertIn("document.pdf", outpath)

    def test_compile_report_writes_each_run_to_its_own_path(self):
        """Two runs of the same report share document_name; each must still get
        its own file, or one could read back the PDF the other just wrote."""
        manager = mocks.MockMontrekReportManager(session_data={})
        manager.append_report_element(mocks.MockReportElement())
        latex_manager = LatexReportManager(manager)
        first_path = latex_manager.compile_report()
        second_path = latex_manager.compile_report()
        self.assertNotEqual(first_path, second_path)
        self.assertEqual(os.path.basename(first_path), "document.pdf")
        self.assertEqual(os.path.basename(second_path), "document.pdf")
        self.assertTrue(os.path.exists(first_path))
        self.assertTrue(os.path.exists(second_path))
