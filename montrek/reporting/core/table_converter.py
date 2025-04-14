from typing import Any
from baseclasses.typing import TableElementsType
from django.db.models import QuerySet
from reporting.core.text_converter import HtmlLatexConverter
from reporting.dataclasses import table_elements as te


class LatexTableConverter:
    def __init__(
        self,
        table_title: str,
        table_elements: TableElementsType,
        table: QuerySet | dict,
    ) -> None:
        self.table_title = table_title
        self.table_elements = table_elements
        self.table = table
        self.column_sizer: dict[str, list[int]] = {}

    def to_latex(self) -> str:
        table_str = self.get_table_str()
        table_start_str = self.get_table_start_str()
        table_end_str = self.get_table_end_str()

        latex_str = table_start_str
        latex_str += table_str
        latex_str += table_end_str
        return latex_str

    def get_table_start_str(self) -> str:
        table_start_str = "\n\\begin{table}[H]\n\\centering\n\\small\n"
        table_start_str += "\\arrayrulecolor{lightgrey}\n"
        table_start_str += "\\setlength{\\tabcolsep}{1pt}\n"
        table_start_str += "\\renewcommand{\\arraystretch}{0.5}\n"
        table_start_str += f"\\caption{{{self.table_title}}}\n"
        table_start_str += "\\begin{tabularx}{\\textwidth}{|"
        column_def_str = ""
        column_header_str = "\\rowcolor{blue}"
        column_sizes = self.get_column_sizes()

        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            column_size = column_sizes[table_element.name]
            column_def_str += f">{{\\hsize={column_size}\\hsize}}X|"
            element_header = HtmlLatexConverter.convert(table_element.name)
            column_header_str += f"\\color{{white}}\\textbf{{{element_header}}} & "
        table_start_str += column_def_str
        table_start_str += "}\n\\hline\n"
        table_start_str += column_header_str[:-2] + "\\\\\n\\hline\n"
        return table_start_str

    def get_table_end_str(self) -> str:
        return "\\end{tabularx}\n\\end{table}\n\n"

    def get_table_str(self) -> str:
        table_str = ""

        for i, query_object in enumerate(self.table):
            if i % 2 == 0:
                table_str += "\\rowcolor{lightblue}"
            for table_element in self.table_elements:
                if isinstance(table_element, te.LinkTableElement):
                    continue
                self.add_to_column_sizer(table_element, query_object)
                table_str += table_element.get_attribute(query_object, "latex")
            table_str = table_str[:-2] + "\\\\\n\\hline\n"
            if (i + 1) % 25 == 0:
                table_str += self.get_table_end_str()
                table_str += self.get_table_start_str()
        return table_str

    def add_to_column_sizer(self, table_element: te.TableElement, query_object: Any):
        field = table_element.name
        value_len = table_element.get_value_len(query_object)
        if field not in self.column_sizer:
            self.column_sizer[field] = [value_len]
        else:
            self.column_sizer[field].append(value_len)

    def get_column_sizes(self):
        total_size = 0
        max_col_size = {}
        for col in self.column_sizer:
            max_val = max(self.column_sizer[col])
            max_col_size[col] = max_val
            total_size += max_val
        max_col_size, total_size = self._adjust_col_size(max_col_size, total_size)
        return {
            col: self._get_adj_col_size(val, max_col_size, total_size)
            for col, val in max_col_size.items()
        }

    def _get_adj_col_size(self, val: int, max_col_size: dict, total_size: int) -> float:
        return val / total_size * len(max_col_size)

    def _adjust_col_size(self, max_col_size: dict, total_size: int):
        cols_len = len(max_col_size)
        adj_total_size = 0
        for col, val in max_col_size.items():
            val = min(val, total_size / cols_len)
            adj_total_size += val
            max_col_size[col] = val
        return max_col_size, adj_total_size
