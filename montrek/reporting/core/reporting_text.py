from reporting.constants import ReportingTextType
from reporting.core.reporting_protocols import ReportingElement
from reporting.core.reporting_mixins import ReportingChecksMixin


class ReportingTextParagraph(ReportingElement, ReportingChecksMixin):
    def __init__(self, text_type: ReportingTextType = ReportingTextType.PLAIN):
        self.text = None
        self.text_type = text_type

    def generate(self, data: str) -> None:
        self.text = data

    def format_latex(self) -> str:
        self._check_for_generating()
        if self.text_type == ReportingTextType.PLAIN:
            return f"{self.text}\n\n"
        return self.text

    def format_html(self) -> str:
        return self._format_to_html()

    def format_mail(self) -> str:
        return self._format_to_html()

    def _format_to_html(self) -> str:
        self._check_for_generating()
        if self.text_type == ReportingTextType.PLAIN:
            return f"<p>{self.text}</p>"
        return self.text
