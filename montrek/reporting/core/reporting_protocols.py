from typing import Protocol


class ReportingElement(Protocol):
    def to_latex(self) -> str: ...

    def to_html(self) -> str: ...
