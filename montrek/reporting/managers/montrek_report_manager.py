from typing import Protocol
from baseclasses.managers.montrek_manager import MontrekManager


class ReportElementProtocol(Protocol):
    def to_html(self) -> str:
        ...

    def to_latex(self) -> str:
        ...


class MontrekReportManager(MontrekManager):
    def __init__(self, session_data: dict[str, str], **kwargs) -> None:
        super().__init__(session_data=session_data, **kwargs)
        self._report_elements = []

    @property
    def report_elements(self) -> list[ReportElementProtocol, ...]:
        return self._report_elements

    def append_report_element(self, report_element: ReportElementProtocol) -> None:
        self._report_elements.append(report_element)

    def compile_report(self) -> str:
        return "MontrekReportManager: No report compiled!!"
