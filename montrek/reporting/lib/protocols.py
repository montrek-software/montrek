from typing import Protocol


class ReportElementProtocol(Protocol):
    def to_html(self) -> str:
        ...

    def to_latex(self) -> str:
        ...
