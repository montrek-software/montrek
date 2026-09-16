import datetime
import math
from typing import Any

import pandas as pd
from baseclasses.managers.montrek_manager import MontrekManager
from django.template.loader import get_template
from baseclasses.typing import TableElementsType
from reporting.core import reporting_text as rt
from reporting.core.text_converter import HtmlTextConverter, LaTeXEscaper
from reporting.dataclasses import table_elements as te
from reporting.dataclasses.display_field import DisplayField
from reporting.lib.protocols import ReportElementProtocol
from reporting.managers.excel_export import ExcelSheetMixin
from reporting.modules.excel_formatter import MontrekDetailsExcelFormatter


class MontrekDetailsManager(ExcelSheetMixin, MontrekManager):
    table_cols: int = 2
    header_col_width: float = 0.3
    table_title: str = ""
    document_title: str = "Montrek Details"
    document_name: str = "details"
    draft: bool = False
    # The sheet is a label/value grid rather than a table, so the frame's
    # column names are not a header row and the formatting differs.
    excel_formatter_class = MontrekDetailsExcelFormatter
    excel_header = False

    def __init__(self, *args, object_query=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Reuse an already fetched row (e.g. from MontrekDetailView's hub pk
        # resolution) instead of re-running the annotated repository query.
        self.object_query = (
            object_query
            if object_query is not None
            else self.get_object_from_pk(self.session_data.get("pk", "Unknown"))
        )
        self.row_size = math.ceil(len(self.table_elements) / self.table_cols)

    @property
    def table_elements(self) -> TableElementsType:
        return ()

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    def get_details_data(self) -> list[list[DisplayField]]:
        return self.arrange_in_grid(
            [
                table_element.get_display_field(self.object_query)
                for table_element in self.table_elements
            ]
        )

    def arrange_in_grid(self, items: list) -> list[list]:
        """Lay items out down the columns, the way the HTML view reads.

        Shared with the Excel export, so the sheet keeps the order and shape
        of the block on screen.
        """
        rows = []
        total = len(items)
        rows_per_col = (total + self.table_cols - 1) // self.table_cols

        for row_index in range(rows_per_col):
            row = []
            for col_index in range(self.table_cols):
                idx = col_index * rows_per_col + row_index
                if idx < total:
                    row.append(items[idx])
            rows.append(row)

        return rows

    @property
    def excel_table_elements(self) -> TableElementsType:
        """Icon links carry no value and nothing to click in a spreadsheet,
        so they are left out - as they are in a table export."""
        return [
            table_element
            for table_element in self.table_elements
            if not isinstance(table_element, te.LinkTableElement)
        ]

    def get_excel_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.get_excel_rows())

    def get_excel_rows(self) -> list[list]:
        """The label/value pairs of the HTML grid, a pair per grid column."""
        pairs = [
            (table_element.name, self._get_excel_value(table_element))
            for table_element in self.excel_table_elements
        ]
        rows = []
        for grid_row in self.arrange_in_grid(pairs):
            row: list[Any] = []
            for label, value in grid_row:
                row += [label, value]
            # Short last rows are padded so every row has the same cells and
            # the label columns stay where the formatter expects them.
            row += [None] * (2 * self.table_cols - len(row))
            rows.append(row)
        return rows

    def get_excel_cell_formats(self) -> dict[tuple[int, int], str | None]:
        """The number format of each value cell, keyed by its position.

        A value column holds a different field in every row, so the format
        cannot be carried per column the way a table's is.
        """
        cell_formats = {}
        for row_index, grid_row in enumerate(
            self.arrange_in_grid(self.excel_table_elements), start=1
        ):
            for col_index, table_element in enumerate(grid_row):
                cell_formats[(row_index, 2 * col_index + 1)] = (
                    table_element.excel_format_str
                )
        return cell_formats

    def get_excel_formatter(self) -> MontrekDetailsExcelFormatter:
        return self.excel_formatter_class(self.get_excel_cell_formats())

    def _get_excel_value(self, table_element) -> Any:
        """The raw value, not the rendered cell: numbers have to stay numbers
        for their number format to mean anything."""
        return HtmlTextConverter.convert(table_element.get_value(self.object_query))

    def get_context_data(self):
        details_data = self.get_details_data()
        col_widths = 100 / self.table_cols
        return {
            "details_data": details_data,
            "col_range": range(self.table_cols),
            "col_widths_head": int(self.header_col_width * col_widths),
            "col_widths_body": int((1 - self.header_col_width) * col_widths),
        }

    def to_html(self) -> str:
        template = get_template("tables/details_table.html")
        return template.render(context=self.get_context_data())

    def to_pdf_html(self) -> str:
        return self.to_html()

    def to_latex(self) -> str:
        latex_str = ""
        minipage_width = 0.98 / self.table_cols
        for i in range(self.table_cols):
            latex_str += f"\\begin{{minipage}}[t]{{{minipage_width}\\textwidth}}\n"
            latex_str += "\\begin{table}[H]\n\\centering\n\\montrektablesetup\n"
            latex_str += "\\arrayrulecolor{bordercolor}\n"
            latex_str += f"\\caption{{{self.table_title}}}\n"
            latex_str += "\\begin{tabularx}{\\textwidth}{"

            column_format = ">{\\hsize=0.666\\hsize}X >{\\raggedleft\\arraybackslash\\hsize=1.333\\hsize}X"
            latex_str += column_format + "}\n\\hline\n"

            start_idx = self.row_size * i
            end_idx = min(self.row_size * (i + 1), len(self.table_elements))
            for table_element in self.table_elements[start_idx:end_idx]:
                element_name = LaTeXEscaper.escape(table_element.name)
                element_attribute = table_element.get_attribute(
                    self.object_query, "latex"
                )[:-2]

                latex_str += (
                    f"\\montrekdetailsheadcell{{{element_name}}}"
                    f" & {element_attribute} \\\\\n\\hline\n"
                )

            latex_str += "\\end{tabularx}\n\\end{table}\n"
            latex_str += "\\end{minipage}"
        return latex_str

    def to_json(self) -> dict:
        out_json = {}
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
                if isinstance(value, datetime.datetime | datetime.date):
                    value = value.isoformat()

                out_json[table_element.attr] = value
        return out_json
