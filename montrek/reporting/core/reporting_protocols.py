from typing import Protocol


class ReportingElement(Protocol):
    def format_latex(self) -> str: ...

    def format_html(self) -> str: ...
