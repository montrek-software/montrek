import os

from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.tests import mocks
from testing.decorators.object_storage import object_storage


def mock_latex_manager() -> LatexReportManager:
    # A fresh manager per compile, as for two separate requests: to_latex()
    # consumes the report elements, so a second compile of the same manager
    # would render an empty document.
    manager = mocks.MockMontrekReportManager(session_data={})
    manager.append_report_element(mocks.MockReportElement())
    return LatexReportManager(manager)


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

    @override_settings(FONT_NAME="")
    def test_main_font_defaults_to_arial(self):
        manager = mocks.MockMontrekReportManager(session_data={})
        generated_report_tex = LatexReportManager(manager).generate_report()
        self.assertIn("\\setmainfont{Arial}", generated_report_tex)

    @override_settings(FONT_NAME="Century Gothic")
    def test_main_font_uses_the_configured_font_name(self):
        manager = mocks.MockMontrekReportManager(session_data={})
        generated_report_tex = LatexReportManager(manager).generate_report()
        self.assertIn("\\setmainfont{Century Gothic}", generated_report_tex)
        self.assertNotIn("Arial", generated_report_tex)

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

        first_path = mock_latex_manager().compile_report()
        second_path = mock_latex_manager().compile_report()
        self.assertIsNotNone(first_path)
        self.assertIsNotNone(second_path)
        self.assertNotEqual(first_path, second_path)
        self.assertEqual(os.path.basename(first_path), "document.pdf")
        self.assertEqual(os.path.basename(second_path), "document.pdf")
        self.assertTrue(os.path.exists(first_path))
        self.assertTrue(os.path.exists(second_path))

    def test_compile_pdf_returns_the_pdf_named_after_the_document(self):
        pdf = mock_latex_manager().compile_pdf()
        self.assertIsNotNone(pdf)
        self.assertEqual(pdf.name, "document.pdf")
        self.assertTrue(pdf.read().startswith(b"%PDF"))

    def test_compile_pdf_returns_none_when_latex_fails(self):
        manager = mocks.MockMontrekReportManager(session_data={})
        latex_manager = LatexReportManager(manager)
        latex_manager.generate_report = lambda: "\\undefinedcommand"
        self.assertIsNone(latex_manager.compile_pdf())
        self.assertIn("LaTeX compilation failed", manager.messages[-1].message)

    @object_storage
    def test_store_pdf_saves_each_compile_under_its_own_name(self):
        first_name = mock_latex_manager().store_pdf()
        second_name = mock_latex_manager().store_pdf()
        self.assertNotEqual(first_name, second_name)
        for name in (first_name, second_name):
            self.assertTrue(name.startswith("latex/"))
            self.assertTrue(name.endswith("/document.pdf"))
            with default_storage.open(name, "rb") as pdf:
                self.assertTrue(pdf.read().startswith(b"%PDF"))
