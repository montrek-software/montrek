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

    def to_latex(self) -> str:
        table_start_str = "\n\\begin{table}[H]\n\\centering\n\\small\n"
        table_start_str += "\\arrayrulecolor{lightgrey}\n"
        table_start_str += "\\setlength{\\tabcolsep}{1pt}\n"
        table_start_str += "\\renewcommand{\\arraystretch}{0.5}\n"
        table_start_str += f"\\caption{{{self.table_title}}}\n"
        table_start_str += "\\begin{tabularx}{\\textwidth}{|"
        table_end_str = "\\end{tabularx}\n\\end{table}\n\n"

        column_def_str = ""
        column_header_str = "\\rowcolor{blue}"

        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            column_def_str += "X|"
            element_header = HtmlLatexConverter.convert(table_element.name)
            column_header_str += f"\\color{{white}}\\textbf{{{element_header}}} & "
        table_start_str += column_def_str
        table_start_str += "}\n\\hline\n"
        table_start_str += column_header_str[:-2] + "\\\\\n\\hline\n"
        table_str = ""

        for i, query_object in enumerate(self.table):
            if i % 2 == 0:
                table_str += "\\rowcolor{lightblue}"
            for table_element in self.table_elements:
                if isinstance(table_element, te.LinkTableElement):
                    continue
                table_str += table_element.get_attribute(query_object, "latex")
            table_str = table_str[:-2] + "\\\\\n\\hline\n"
            if (i + 1) % 25 == 0:
                table_str += table_end_str
                table_str += table_start_str

        latex_str = table_start_str
        latex_str += table_str
        latex_str += table_end_str
        return latex_str
