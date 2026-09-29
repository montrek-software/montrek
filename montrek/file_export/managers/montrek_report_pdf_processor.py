import logging
import os

from django.core.files.base import ContentFile
from reporting.managers.latex_report_manager import LatexReportManager

from file_export.managers.file_export_processor_abc import FileExportProcessorABC
from reporting.managers.montrek_report_manager import MontrekReportManager

logger = logging.getLogger(__name__)


class MontrekReportPdfProcessor(FileExportProcessorABC):
    report_manager: type[MontrekReportManager]
    report_name: str

    def process(self) -> bool:
        try:
            report_manager = LatexReportManager(self.get_report_manager())
            pdf_path = report_manager.compile_report()
            if pdf_path is None:
                self.set_message(f"Kein {self.report_name} generiert.")
                return False

            with open(pdf_path, "rb") as f:
                self.set_result_file(
                    ContentFile(f.read(), name=os.path.basename(pdf_path))
                )
            self.set_message(f"{self.report_name} generiert.")
        except Exception:  # noqa: BLE001
            logger.exception(f"{self.report_name} export failed")
            self.set_message("Export fehlgeschlagen.")
            return False
        return True

    def get_report_manager(self) -> MontrekReportManager:
        return self.report_manager(self.session_data)
