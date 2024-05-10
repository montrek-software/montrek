from dataclasses import dataclass
from reporting.managers.montrek_report_manager import ReportElementProtocol


class ReportGridElements:
    report_grid_elements_containter = []

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        if row + 1 >= len(self.report_grid_elements_containter):
            for _ in range(row + 1):
                self.report_grid_elements_containter.append([])
        if col + 1 >= len(self.report_grid_elements_containter[row]):
            for _ in range(col + 1):
                self.report_grid_elements_containter[row].append(
                    EmptyReportGridElement()
                )
        self.report_grid_elements_containter[row][col] = report_element


class ReportGridLayout:
    report_grid_elements = ReportGridElements()

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements.add_report_grid_element(report_element, row, col)

    def to_html(self):
        ...

    def to_latex(self):
        ...


class EmptyReportGridElement:
    def to_html(self) -> str:
        return ""

    def to_latex(self) -> str:
        return ""
