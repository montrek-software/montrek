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

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements_container[row][col] = report_element


class ReportGridLayout:
    def __init__(self, no_of_rows: int, no_of_cols: int, is_nested=False):
        self.report_grid_elements = ReportGridElements(no_of_rows, no_of_cols)
        self.is_nested = is_nested

    def add_report_grid_element(
        self, report_element: ReportElementProtocol, row: int, col: int
    ):
        self.report_grid_elements.add_report_grid_element(report_element, row, col)

    def to_html(self):
        html_str = '<div><table id="noStyleTable">'
        for row in self.report_grid_elements.report_grid_elements_container:
            html_str += "<tr>"
            for element in row:
                html_str += f"<td>{element.to_html()}</td>"
            html_str += "</tr>"
        html_str += "</table></div>"
        return html_str

    def to_latex(self):
        col_str = self._get_latex_column_definition()
        latex_str = "\n\n" if self.is_nested else "\n\n\\begin{table}[H]"

        latex_str += f"\n\\begin{{tabular}}{{ {col_str} }}"
        for row in self.report_grid_elements.report_grid_elements_container:
            latex_str += "\n"
            for element in row:
                latex_str += f"{element.to_latex()} & "
            latex_str = latex_str[:-3] + " \\\\\n"
        latex_str += "\n\\end{tabular}"
        if self.is_nested:
            latex_str += "\n"
        else:
            latex_str += "\n\\end{table}\n\n"
        return latex_str

    def _get_latex_column_definition(self) -> str:
        # If the grid is top level, it should span over the complete textwidth
        # and the last column should be rightaligned
        no_of_columns = self.report_grid_elements.no_of_cols
        col_tag = (
            "l"
            if self.is_nested
            else f">{{\\raggedright\\arraybackslash}}p{{ {(0.97/no_of_columns):.5f}\\textwidth}}"
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
