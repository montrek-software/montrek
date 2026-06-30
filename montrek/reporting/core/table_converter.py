from typing import Any, Literal

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
        rows_per_page: int = 25,
    ) -> None:
        self.table_title = table_title
        self.table_elements = table_elements
        self.table = table
        if rows_per_page < 1:
            raise ValueError("rows_per_page must be >= 1")
        self.rows_per_page = rows_per_page
        self.column_sizer: dict[int, list[int]] = {}

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
        table_start_str += "\\arrayrulecolor{bordercolor}\n"
        table_start_str += "\\setlength{\\tabcolsep}{5pt}\n"
        table_start_str += "\\renewcommand{\\arraystretch}{1.2}\n"
        table_start_str += f"\\caption{{{self.table_title}}}\n"
        table_start_str += "\\begin{tabularx}{\\textwidth}{"
        column_def_str = ""
        column_header_str = "\\rowcolor{surfacemuted}"
        column_sizes = self.get_column_sizes()

        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            column_size = column_sizes.get(col_idx, 0)
            column_def_str += f">{{\\hsize={column_size}\\hsize}}X "
            element_header = HtmlLatexConverter.convert(table_element.name)
            element_header = " ".join(
                [f"\\mbox{{{head}}}" for head in element_header.split(" ")]
            )
            column_header_str += (
                f"\\textcolor{{textmuted}}{{\\textbf{{{element_header}}}}} & "
            )
            col_idx += 1
        table_start_str += column_def_str.rstrip()
        table_start_str += "}\n\\hline\n"
        table_start_str += column_header_str[:-2] + "\\\\\n"
        table_start_str += (
            "\\arrayrulecolor{primary}\\hline\\arrayrulecolor{bordercolor}\n"
        )
        return table_start_str

    def get_table_end_str(self) -> str:
        return "\\end{tabularx}\n\\end{table}\n\n"

    def get_table_str(self) -> str:
        table_str = ""
        self._seed_column_sizer_from_headers()

        for i, query_object in enumerate(self.table):
            col_idx = 0
            for table_element in self.table_elements:
                if isinstance(table_element, te.LinkTableElement):
                    continue
                self.add_to_column_sizer(table_element, query_object, col_idx)
                table_str += table_element.get_attribute(query_object, "latex")
                col_idx += 1
            table_str = table_str[:-2] + "\\\\\n\\hline\n"
            if (i + 1) % self.rows_per_page == 0:
                table_str += self.get_table_end_str()
                table_str += "\\newpage\n"
                table_str += self.get_table_start_str()
        return table_str

    def _seed_column_sizer_from_headers(self) -> None:
        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            self.column_sizer[col_idx] = [len(str(table_element.name))]
            col_idx += 1

    def add_to_column_sizer(
        self, table_element: te.TableElement, query_object: Any, col_idx: int
    ):
        value_len = table_element.get_value_len(query_object)
        if col_idx not in self.column_sizer:
            self.column_sizer[col_idx] = [value_len]
        else:
            self.column_sizer[col_idx].append(value_len)

    def get_column_sizes(self):
        total_size = 0
        max_col_size = {}
        for col in self.column_sizer:
            max_val = max(self.column_sizer[col])
            max_col_size[col] = max_val
            total_size += max_val
        max_col_size, total_size = self._adjust_col_size(max_col_size, total_size)
        return {
            col: self.get_adj_col_size(val, max_col_size, total_size)
            for col, val in max_col_size.items()
        }

    @staticmethod
    def get_adj_col_size(
        val: int, max_col_size: dict, total_size: float | Literal[0]
    ) -> float:
        if total_size == 0:
            return 0
        return val / total_size * len(max_col_size)

    def _adjust_col_size(self, max_col_size: dict, total_size: int):
        cols_len = len(max_col_size)
        adj_total_size = 0
        for col, val in max_col_size.items():
            min_size = total_size / (5 * cols_len)
            max_size = 3 * total_size / cols_len
            val = min(max(val, min_size), max_size)
            adj_total_size += val
            max_col_size[col] = val
        return max_col_size, adj_total_size
