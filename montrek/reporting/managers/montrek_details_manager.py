import datetime
import math

from baseclasses.managers.montrek_manager import MontrekManager
from django.template.loader import get_template
from reporting.core import reporting_text as rt
from reporting.dataclasses import table_elements as te
from reporting.dataclasses.display_field import DisplayField
from reporting.lib.protocols import ReportElementProtocol


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

    def get_details_data(self) -> list[list[DisplayField]]:
        elements = [
            DisplayField(
                table_element=table_element,
                value=table_element.get_attribute(self.object_query, "html"),
            )
            for table_element in self.table_elements
        ]

        rows = []
        total = len(elements)
        rows_per_col = (total + self.table_cols - 1) // self.table_cols

        for row_index in range(rows_per_col):
            row = []
            for col_index in range(self.table_cols):
                idx = col_index * rows_per_col + row_index
                if idx < total:
                    row.append(elements[idx])
            rows.append(row)

        return rows

    def to_html(self) -> str:
        template = get_template("tables/details_table.html")
        bt_col_size = 12 // self.table_cols
        details_data = self.get_details_data()
        return template.render(
            context={
                "bt_col_size": bt_col_size,
                "table_cols": self.table_cols,
                "details_data": details_data,
            }
        )

    def to_latex(self) -> str:
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
            column_format = "|>{\\hsize=0.666\\hsize}X|>{\\raggedleft\\arraybackslash\\hsize=1.333\\hsize}X|"
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
            latex_str += "\\end{minipage}"
        with open("test.txt", "w") as f:
            f.write(latex_str)
        return latex_str

    def to_json(self) -> dict:
        out_json = dict()
        for table_element in self.table_elements:
            if isinstance(table_element, (te.LinkTableElement)):
                continue
            if isinstance(table_element, te.LinkTextTableElement):
                out_json[table_element.text] = table_element.get_value(
                    self.object_query
                )
            elif isinstance(table_element, te.LinkListTableElement):
                values = table_element.get_value(self.object_query)

                out_json[table_element.text] = str([val[1] for val in values])
            else:
                value = table_element.get_value(self.object_query)
                if isinstance(value, (datetime.datetime, datetime.date)):
                    value = value.isoformat()

                out_json[table_element.attr] = value
        return out_json
