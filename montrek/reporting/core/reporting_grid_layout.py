from math import floor
from dataclasses import dataclass
from reporting.core.reporting_text import ContextTypes, ReportingElement

from reporting.managers.montrek_report_manager import ReportElementProtocol


class ReportGridElements:
    def __init__(self, no_of_rows: int, no_of_cols: int):
        self.report_grid_elements_container = []
        self.no_of_cols = no_of_cols
        self.no_of_rows = no_of_rows
        for _ in range(no_of_rows):
            self.report_grid_elements_container.append(
                [EmptyReportGridElement() for _ in range(no_of_cols)]
            )
        self.width = 0.98 / no_of_cols

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        try:
            self.report_grid_elements_container[row][col] = report_element
        except IndexError as err:
            raise IndexError(
                f"Row index ({row}) or column index ({col}) does not match grid dimensions({self.no_of_rows},{self.no_of_cols})"
            ) from err


@dataclass
class GridRowDisplay:
    """
    Represents a single row in the report grid layout.

    Attributes
    ----------
    html_elements:
        List of rendered HTML fragments for each element in the row, in
        display order.
    col_len:
        Bootstrap column width (out of 12) assigned to each element in the
        row. This is typically computed as ``floor(12 / len(html_elements))``.
    """
    html_elements: list[str]
    col_len: int


class ReportGridLayout(ReportingElement):
    template_name = "grid"

    def __init__(self, no_of_rows: int, no_of_cols: int, is_nested=False):
        self.report_grid_elements = ReportGridElements(no_of_rows, no_of_cols)
        self.is_nested = is_nested

    @property
    def width(self):
        return self.report_grid_elements.width

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements.add_report_grid_element(report_element, row, col)

    def get_context_data(self) -> ContextTypes:
        grid_rows = []
        for row in self.report_grid_elements.report_grid_elements_container:
            html_elements = [element.to_html() for element in row]
            col_len = floor(12 / len(html_elements))
            grid_rows.append(
                GridRowDisplay(html_elements=html_elements, col_len=col_len)
            )

        return {"grid_rows": grid_rows}

    def to_latex(self):
        col_str = self._get_latex_column_definition()
        latex_str = "\n\n" if self.is_nested else "\n\n\\begin{table}[H]"

        latex_str += f"\n\\begin{{tabular}}{{ {col_str} }}\n"
        for row in self.report_grid_elements.report_grid_elements_container:
            latex_str += "\n"
            for element in row:
                latex_str += f"\\begin{{minipage}}[t]{{{self.report_grid_elements.width}\\textwidth}}\n"
                latex_str += f"{element.to_latex()} "
                latex_str += "\\end{minipage} &\n"
            latex_str = latex_str[:-3] + " \\\\\n"
        latex_str += "\n\\end{tabular}"
        if self.is_nested:
            latex_str += "\n"
        else:
            latex_str += "\n\\end{table}\n\n"
        return latex_str

    def to_json(self) -> dict[str, list]:
        return_list = []
        for row in self.report_grid_elements.report_grid_elements_container:
            row_list = []
            for element in row:
                row_list.append(element.to_json())
            return_list.append(row_list)
        return {"report_grid_elements": return_list}

    def _get_latex_column_definition(self) -> str:
        # If the grid is top level, it should span over the complete textwidth
        # and the last column should be rightaligned
        no_of_columns = self.report_grid_elements.no_of_cols
        col_tag = (
            "l"
            if self.is_nested
            else f">{{\\raggedright\\arraybackslash}}p{{ {(self.width):.5f}\\textwidth}}"
        )
        col_str = ""
        for i in range(no_of_columns):
            tag = col_tag
            if i == no_of_columns - 1:
                tag = tag.replace("\\raggedright", "\\raggedleft")
            col_str += tag
        return col_str


class EmptyReportGridElement:
    def to_html(self) -> str:
        return ""

    def to_latex(self) -> str:
        return ""

    def to_json(self) -> dict:
        return {"empty_report_grid_element": []}
