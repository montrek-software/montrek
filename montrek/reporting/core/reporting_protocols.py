from typing import Protocol
from typing import Union
from reporting.core.reporting_data import ReportingData


class ReportingElement(Protocol):
    def generate(self, data: Union[ReportingData, str]) -> None:
        ...

    def format_latex(self) -> str:
        ...

    def format_html(self) -> str:
        ...

    def format_mail(self) -> str:
        ...
