from dataclasses import dataclass
from reporting.managers.montrek_report_manager import ReportElementProtocol


class ReportGridElements:
    def __init__(self, no_of_rows: int, no_of_cols: int):
        self.report_grid_elements_container = []
        for _ in range(no_of_rows):
            self.report_grid_elements_container.append(
                [EmptyReportGridElement() for _ in range(no_of_cols)]
            )

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements_container[row][col] = report_element


class ReportGridLayout:
    def __init__(self, no_of_rows: int, no_of_cols: int):
        self.report_grid_elements = ReportGridElements(no_of_rows, no_of_cols)

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements.add_report_grid_element(report_element, row, col)

    def to_html(self):
        html_str = "<div><table>"
        for row in self.report_grid_elements.report_grid_elements_container:
            html_str += "<tr>"
            for element in row:
                html_str += f"<td>{element.to_html()}</td>"
            html_str += "</tr>"
        html_str += "</table></div>"
        return html_str

    def to_latex(self):
        col_str = "l" * len(
            max(self.report_grid_elements.report_grid_elements_container, key=len)
        )
        latex_str = f"\n\\begin{{tabular}}{{ {col_str} }}"
        for row in self.report_grid_elements.report_grid_elements_container:
            latex_str += "\n"
            for element in row:
                latex_str += f"{element.to_latex()} & "
            latex_str = latex_str[:-3] + " \\\\\n"
        latex_str += "\n\\end{tabular}"
        return latex_str


class EmptyReportGridElement:
    def to_html(self) -> str:
        return ""

    def to_latex(self) -> str:
        return ""
