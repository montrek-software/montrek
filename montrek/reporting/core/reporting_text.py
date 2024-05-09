from reporting.constants import ReportingTextType, TextType
from reporting.core.reporting_protocols import ReportingElement
from reporting.core.reporting_mixins import ReportingChecksMixin
from reporting.managers.montrek_report_manager import (
    ReportElementProtocol,
)


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


class ReportingParagraph(ReportElementProtocol):
    def __init__(
        self,
        text: str,
        reporting_text_type: ReportingTextType = ReportingTextType.HTML,
    ):
        self.text = text
        self.reporting_text_type = reporting_text_type

    def to_latex(self) -> str:
        match self.reporting_text_type:
            case ReportingTextType.PLAIN:
                text = self.text
            case ReportingTextType.HTML:
                text = HtmlLatexConverter.convert(self.text)
            case _:
                text = f"\\textbf{{\\color{{red}} Unknown Text Type {self.reporting_text_type}"
        return f"{text}\\newline\\newline"

    def to_html(self) -> str:
        return f"<div><p>{self.text}</p></div>"


class ReportingHeader1:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h1>{self.text}</h1>"

    def to_latex(self) -> str:
        return f"\\section{{{self.text}}}"


class ReportingHeader2:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h2>{self.text}</h2>"

    def to_latex(self) -> str:
        return f"\\textbf{{\\color{{blue}} { self.text } }}\\newline"
