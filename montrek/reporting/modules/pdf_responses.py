from typing import Any

from baseclasses.dataclasses.montrek_message import MontrekMessageError
from django.http import FileResponse, HttpResponse
from django.http.response import HttpResponseBase

from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.weasyprint_pdf_manager import WeasyPrintPdfManager


class PdfResponses:
    """The PDF exports of the base views, registered in ``ReportingConfig``."""

    @staticmethod
    def weasyprint(manager: Any) -> HttpResponse | None:
        """HTML → PDF via WeasyPrint."""
        pdf_bytes = WeasyPrintPdfManager(manager).generate_pdf()
        if not pdf_bytes:
            manager.messages.append(
                MontrekMessageError("PDF generation failed. Please try again.")
            )
            return None
        filename = f"{manager.document_name}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def latex(manager: Any) -> HttpResponseBase | None:
        """Full XeLaTeX typesetting."""
        pdf = LatexReportManager(manager).compile_pdf()
        if pdf is None:
            return None
        return FileResponse(pdf, content_type="application/pdf", filename=str(pdf.name))
