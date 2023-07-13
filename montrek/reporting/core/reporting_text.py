from enum import Enum
from reporting.core.reporting_protocols import ReportingElement

class ReportingTextType(Enum):
    PLAIN = 0
    MARKDOWN = 1
    HTML = 2
    LATEX = 3

class ReportingTextParagraph(ReportingElement):
    def __init__(self, 
                 text: str,
                 text_type: ReportingTextType = ReportingTextType.PLAIN):
        self.text = text
        self.text_type = text_type

    def format_latex(self) -> str:
        if self.text_type == ReportingTextType.PLAIN:
            return f"{self.text}\n\n"
        return self.text

    def format_html(self) -> str:
        return self._format_to_html()

    def format_mail(self) -> str:
        return self._format_to_html()

    def _format_to_html(self) -> str:
        if self.text_type == ReportingTextType.PLAIN:
            return f"<p>{self.text}</p>"
        return self.text
