from collections.abc import Iterable
from baseclasses.managers.montrek_manager import MontrekManager
from reporting.core import reporting_text as rt
from reporting.lib.protocols import (
    ReportElementProtocol,
)


class MontrekReportManager(MontrekManager):
    document_name = "document"
    document_title = "Montrek Report"
    draft = False

    def __init__(self, session_data: dict[str, str], **kwargs) -> None:
        super().__init__(session_data=session_data, **kwargs)
        self._report_elements = []

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    @property
    def report_elements(self) -> list[ReportElementProtocol, ...]:
        return self._report_elements

    def append_report_element(
        self, report_element: ReportElementProtocol | list[ReportElementProtocol]
    ) -> None:
        if isinstance(report_element, Iterable):
            self._report_elements.extend(report_element)
        else:
            self._report_elements.append(report_element)

    def collect_report_elements(self) -> None:
        raise NotImplementedError("This method must be implemented in the child class")

    def to_html(self) -> str:
        html_str = ""
        self.collect_report_elements()
        for report_element in self.report_elements:
            html_str += report_element.to_html()
        html_str += self._get_footer()
        return html_str

    def to_latex(self) -> str:
        latex_str = ""
        self.collect_report_elements()
        for report_element in self.report_elements:
            latex_str += report_element.to_latex()
        return latex_str

    def _get_footer(self) -> str:
        footer = f'<div style="height:2cm"></div><hr><div style="color:grey">{self.footer_text.to_html()}</div>'
        return footer
