from django.test import TestCase

from file_export.managers.montrek_report_pdf_processor import MontrekReportPdfProcessor
from file_export.tests.mocks import (
    MockPdfReportManager,
    MockReportPdfProcessor,
    MockReportPdfProcessorBrokenLatex,
    MockReportPdfProcessorError,
)

LOGGER_NAME = "file_export.managers.montrek_report_pdf_processor"


class TestMontrekReportPdfProcessorProcess(TestCase):
    def test_attaches_the_compiled_pdf(self):
        processor = MockReportPdfProcessor(None, {})
        self.assertTrue(processor.process())
        self.assertEqual(processor.message, "Mock Report generiert.")
        self.assertIsNotNone(processor.result_file)
        self.assertEqual(processor.result_file.name, "mock_pdf_report.pdf")
        self.assertTrue(processor.result_file.read().startswith(b"%PDF"))

    def test_fails_when_no_pdf_is_produced(self):
        processor = MockReportPdfProcessorBrokenLatex(None, {})
        with self.assertLogs(LOGGER_NAME, level="ERROR") as logs:
            self.assertFalse(processor.process())
        self.assertEqual(processor.message, "Kein Mock Report generiert.")
        self.assertIsNone(processor.result_file)
        # The xelatex output is logged, not dropped.
        self.assertIn("LaTeX compilation failed", logs.output[0])

    def test_fails_when_the_report_run_raises(self):
        processor = MockReportPdfProcessorError(None, {})
        with self.assertLogs(LOGGER_NAME, level="ERROR") as logs:
            self.assertFalse(processor.process())
        self.assertEqual(processor.message, "Export fehlgeschlagen.")
        self.assertIsNone(processor.result_file)
        self.assertIn("Mock Report export failed", logs.output[0])


class TestMontrekReportPdfProcessorGetReportManager(TestCase):
    def test_builds_the_report_manager_from_session_data(self):
        session_data = {"pk": 1}
        report_manager = MockReportPdfProcessor(None, session_data).get_report_manager()
        self.assertIsInstance(report_manager, MockPdfReportManager)
        self.assertIs(report_manager.session_data, session_data)


class TestMontrekReportPdfProcessorSubclassCheck(TestCase):
    def test_subclass_without_report_manager_and_name_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "report_manager, report_name"):

            class IncompleteProcessor(MontrekReportPdfProcessor):
                pass

    def test_subclass_without_report_name_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "must define report_name$"):

            class IncompleteProcessor(MontrekReportPdfProcessor):
                report_manager = MockPdfReportManager
