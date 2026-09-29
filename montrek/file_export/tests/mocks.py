from unittest.mock import MagicMock

from django.core.files.base import ContentFile

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_processor_abc import FileExportProcessorABC
from file_export.managers.montrek_report_pdf_processor import MontrekReportPdfProcessor
from reporting.core.reporting_text import ReportingText
from reporting.managers.montrek_report_manager import MontrekReportManager


# ---- processors ----


class MockFileExportProcessor(FileExportProcessorABC):
    def pre_check(self) -> bool:
        return True

    def process(self) -> bool:
        self.set_result_file(ContentFile(b"col1,col2\n1,2\n", name="export.csv"))
        self.set_message("Export successful")
        return True

    def post_check(self) -> bool:
        return self.result_file is not None


class MockFileExportProcessorFailPreCheck(MockFileExportProcessor):
    def pre_check(self) -> bool:
        self.set_message("Pre Check Failed")
        return False


class MockFileExportProcessorFailProcess(MockFileExportProcessor):
    def process(self) -> bool:
        self.set_message("Process Failed")
        return False


class MockFileExportProcessorFailPostCheck(MockFileExportProcessor):
    def post_check(self) -> bool:
        self.set_message("Post Check Failed")
        return False


class MockFileExportProcessorNoFile(MockFileExportProcessor):
    def process(self) -> bool:
        self.set_message("No file generated")
        return True

    def post_check(self) -> bool:
        return True


# ---- managers (no DB — override all registry operations) ----


class MockFileExportManager(FileExportManagerABC):
    status_field_name = "export_status"
    message_field_name = "export_message"
    do_process_async = False
    registry_repository_class = MagicMock
    processor_class = MockFileExportProcessor

    def __init__(self, session_data):
        super().__init__(session_data)
        self._registry_updates: list[dict] = []

    def _init_registry(self, **kwargs) -> int:
        return 1

    def _load_registry(self) -> None:
        self.registry = MagicMock(pk=1)

    def _update_registry(self, **kwargs) -> None:
        self._registry_updates.append(dict(kwargs))

    def _build_processor(self, pipeline_data) -> FileExportProcessorABC:
        return self.processor_class(self.registry, self.session_data)


class MockFileExportManagerFailPreCheck(MockFileExportManager):
    processor_class = MockFileExportProcessorFailPreCheck


class MockFileExportManagerFailProcess(MockFileExportManager):
    processor_class = MockFileExportProcessorFailProcess


class MockFileExportManagerFailPostCheck(MockFileExportManager):
    processor_class = MockFileExportProcessorFailPostCheck


class MockFileExportManagerNoFile(MockFileExportManager):
    processor_class = MockFileExportProcessorNoFile


# ---- report PDF processors ----


class MockPdfReportManager(MontrekReportManager):
    document_name = "mock_pdf_report"
    document_title = "Mock PDF Report"

    def collect_report_elements(self) -> None:
        self.append_report_element(ReportingText("Mock report content"))


class MockPdfReportManagerBrokenLatex(MockPdfReportManager):
    """The base template opens with the content, so an undefined control
    sequence halts xelatex before any page is shipped: no PDF is written."""

    def to_latex(self) -> str:
        return "\\undefinedcontrolsequence"


class MockPdfReportManagerError(MockPdfReportManager):
    def collect_report_elements(self) -> None:
        raise ValueError("Report data could not be collected")


class MockReportPdfProcessor(MontrekReportPdfProcessor):
    report_manager = MockPdfReportManager
    report_name = "Mock Report"

    def pre_check(self) -> bool:
        return True

    def post_check(self) -> bool:
        return True


class MockReportPdfProcessorBrokenLatex(MockReportPdfProcessor):
    report_manager = MockPdfReportManagerBrokenLatex


class MockReportPdfProcessorError(MockReportPdfProcessor):
    report_manager = MockPdfReportManagerError
