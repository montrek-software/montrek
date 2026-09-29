import logging
import os
from typing import Any

from django.core.files.base import ContentFile
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import MontrekReportManager

from file_export.managers.file_export_processor_abc import FileExportProcessorABC

logger = logging.getLogger(__name__)


class MontrekReportPdfProcessor(FileExportProcessorABC):
    report_manager_class: type[MontrekReportManager]
    report_name: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Checked at class definition: a missing attribute would otherwise
        # only surface mid-export, inside process()'s own error handling.
        missing = [
            attr
            for attr in ("report_manager_class", "report_name")
            if not hasattr(cls, attr)
        ]
        if missing:
            raise TypeError(f"{cls.__name__} must define {', '.join(missing)}")

    def process(self) -> bool:
        try:
            latex_manager = LatexReportManager(self.get_report_manager())
            pdf_path = latex_manager.compile_report()
            if pdf_path is None:
                self._log_compile_errors(latex_manager.report_manager)
                self.set_message(f"Kein {self.report_name} generiert.")
                return False

            with open(pdf_path, "rb") as f:
                self.set_result_file(
                    ContentFile(f.read(), name=os.path.basename(pdf_path))
                )
            self.set_message(f"{self.report_name} generiert.")
        except Exception:
            logger.exception("%s export failed", self.report_name)
            self.set_message("Export fehlgeschlagen.")
            return False
        return True

    def get_report_manager(self) -> MontrekReportManager:
        return self.report_manager_class(self.session_data)

    def _log_compile_errors(self, report_manager: MontrekReportManager) -> None:
        # compile_report() leaves the xelatex output on the report manager's
        # messages; too long for the user-facing message, so it goes to the log.
        details = "\n".join(message.message for message in report_manager.messages)
        logger.error("%s was not compiled: %s", self.report_name, details)
