import math
from baseclasses.managers.montrek_manager import MontrekManager
from reporting.dataclasses import table_elements as te
from reporting.core import reporting_text as rt
from reporting.lib.protocols import (
    ReportElementProtocol,
)


class MontrekDetailsManager(MontrekManager):
    table_cols = 2
    table_title = ""
    document_title = "Montrek Details"
    document_name = "details"
    draft = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_query = self.get_object_from_pk(
            self.session_data.get("pk", "Unknown")
        )
        self.row_size = math.ceil(len(self.table_elements) / self.table_cols)

    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return ()

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    def to_html(self):
        html_str = '<div class="row">'
        bt_col_size = 12 // self.table_cols
        for i in range(self.table_cols):
            html_str += f'<div class="col-md-{bt_col_size}">'
            html_str += '<table class="table table-bordered table-hover">'
            start_idx = self.row_size * i
            end_idx = min(self.row_size * (i + 1), len(self.table_elements))
            for table_element in self.table_elements[start_idx:end_idx]:
                html_str += f"<tr><th>{table_element.name}</th>{table_element.get_attribute(self.object_query, 'html')}</tr>"
            html_str += "</table>"
            html_str += "</div>"
        html_str += "</div>"
        return html_str

    def to_latex(self):
        latex_str = ""
        minipage_width = 0.98 / self.table_cols
        for i in range(self.table_cols):
            latex_str += f"\\begin{{minipage}}[t]{{{minipage_width}\\textwidth}}\n"
            latex_str += "\\begin{table}[H]\n\\centering\n\\small\n"
            latex_str += "\\arrayrulecolor{lightgrey}\n"
            latex_str += "\\setlength{\\tabcolsep}{2pt}\n"
            latex_str += "\\renewcommand{\\arraystretch}{1.0}\n"
            latex_str += f"\\caption{{{self.table_title}}}\n"
            latex_str += "\\begin{tabularx}{\\textwidth}{"

            # Define the column format based on the number of columns
            column_format = "|X|X|"
            latex_str += column_format + "}\n\\hline\n"

            start_idx = self.row_size * i
            end_idx = min(self.row_size * (i + 1), len(self.table_elements))
            for j, table_element in enumerate(self.table_elements[start_idx:end_idx]):
                element_name = table_element.name
                element_attribute = table_element.get_attribute(
                    self.object_query, "latex"
                )[:-2]
                cell_color = "\\cellcolor{lightblue}" if j % 2 == 1 else ""

                latex_str += f"\\cellcolor{{blue}}\\color{{white}}\\textbf{{{element_name}}} &{cell_color} {element_attribute} \\\\\n\\hline\n"

            latex_str += "\\end{tabularx}\n\\end{table}\n"
            latex_str += "\\end{minipage}\n"
        return latex_str
