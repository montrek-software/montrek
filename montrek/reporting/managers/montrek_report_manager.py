from django.conf import settings
import os
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

    def generate_report(self) -> str:
        return "MontrekReportManager: No report compiled!!"


class LatexReportManager(MontrekReportManager):
    latex_template = "montrek_base_template.tex"

    def generate_report(self) -> str:
        content = ""
        for report_element in self.report_elements:
            content += report_element.to_latex()
        template = self.read_template()
        report = template.format(content=content)
        return report

    def read_template(self) -> str:
        template_path = self._get_template_path()
        if template_path is None:
            raise FileNotFoundError(f"Template {self.latex_template} not found")
        with open(template_path, "r") as file:
            return file.read()

    def _get_template_path(self):
        for template_dir in settings.TEMPLATES[0]["DIRS"]:
            potential_path = os.path.join(template_dir, self.latex_template)
            if os.path.exists(potential_path):
                return potential_path
        return None
