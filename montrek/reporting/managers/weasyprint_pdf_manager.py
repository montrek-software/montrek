import logging
import os

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class WeasyPrintPdfManager:
    """Converts a table or details manager to PDF using WeasyPrint (HTML→PDF).

    The manager must expose a ``to_pdf_html()`` method that returns a rendered
    HTML fragment (not a full document).  The full document wrapper (page
    layout, gold-theme CSS, header/footer) is supplied by
    ``pdf/pdf_base.html``.
    """

    template_name = "pdf/pdf_base.html"

    def __init__(self, manager):
        self.manager = manager

    def generate_pdf(self) -> bytes | None:
        try:
            html_str = self._render_html()
            return weasyprint.HTML(
                string=html_str,
                base_url=f"file://{settings.BASE_DIR}/",
            ).write_pdf()
        except Exception:
            logger.exception("WeasyPrint PDF generation failed")
            return None

    def _render_html(self) -> str:
        content = self.manager.to_pdf_html()
        return render_to_string(
            self.template_name,
            {
                "title": self._title,
                "content": content,
                "primary_color": settings.PRIMARY_COLOR,
                "secondary_color": settings.SECONDARY_COLOR,
                "montrek_logo_path": self._montrek_logo_path(),
                "client_logo_path": self._client_logo_path(),
                "page_orientation": getattr(
                    self.manager, "pdf_orientation", "landscape"
                ),
            },
        )

    @property
    def _title(self) -> str:
        return (
            getattr(self.manager, "document_title", None)
            or getattr(self.manager, "table_title", None)
            or ""
        )

    @staticmethod
    def _montrek_logo_path() -> str:
        path = os.path.join(
            settings.BASE_DIR,
            "baseclasses",
            "static",
            "logos",
            "montrek_logo_variant.png",
        )
        return path if os.path.exists(path) else ""

    @staticmethod
    def _client_logo_path() -> str:
        path = getattr(settings, "CLIENT_LOGO_PATH", "")
        if path and os.path.exists(path):
            return path
        return ""
