from typing import Protocol


class ReportingData(Protocol):
    ...


class ReportingElement(Protocol):
    def generate(self, data: ReportingData) -> None:
        ...

    def format_latex(self) -> str:
        ...

    def format_html(self) -> str:
        ...

    def format_mail(self) -> str:
        ...

