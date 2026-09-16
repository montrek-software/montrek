"""Writing managers into Excel workbooks.

Both the table managers and the details managers export the same way - a
frame written into a sheet, then styled by a ``MontrekExcelFormatter`` - and
both can be written into a workbook somebody else opened, so a download can
put a details block and a table side by side as two sheets.
"""

from collections.abc import Mapping
from io import BytesIO
from typing import Protocol

import pandas as pd
from django.http import HttpResponse

from reporting.modules.excel_formatter import MontrekExcelFormatter

ExcelOutput = HttpResponse | BytesIO | str


class ExcelSheetProtocol(Protocol):
    def get_excel_frame(self) -> pd.DataFrame: ...

    def write_excel_sheet(
        self,
        excel_writer: pd.ExcelWriter,
        sheet_name: str = ...,
        show_table_title: bool = ...,
        frame: pd.DataFrame | None = ...,
    ) -> None: ...


def write_excel_workbook(
    output: ExcelOutput,
    sheets: Mapping[str, ExcelSheetProtocol],
    show_table_titles: bool = False,
) -> ExcelOutput:
    """Write one sheet per manager into a single workbook.

    A manager's own ``to_excel`` owns its writer, so calling it once per
    manager would have each one overwrite the workbook the one before it
    wrote. Everything that needs more than one sheet goes through here.

    Every frame is built before the workbook is opened, because openpyxl
    swallows whatever is raised inside the writer's context and fails on the
    way out with "At least one sheet must be visible" instead - hiding the
    error that actually went wrong.
    """
    frames = {name: manager.get_excel_frame() for name, manager in sheets.items()}
    with pd.ExcelWriter(output, engine="openpyxl") as excel_writer:
        for sheet_name, manager in sheets.items():
            manager.write_excel_sheet(
                excel_writer, sheet_name, show_table_titles, frame=frames[sheet_name]
            )
    return output


class ExcelSheetMixin:
    """A manager that can write itself as one sheet of a workbook.

    Subclasses supply the frame to write (``get_excel_frame``) and, where the
    sheet has one, the number format per column (``get_excel_col_formats``).
    ``excel_header`` says whether the frame's column names are a header row:
    a table's are, a details block's label/value grid has none.
    """

    excel_formatter_class: type[MontrekExcelFormatter] = MontrekExcelFormatter
    excel_header: bool = True
    table_title: str = ""

    def to_excel(
        self,
        output: ExcelOutput,
        sheet_name: str = "Montrek Data",
        show_table_title: bool = False,
    ) -> ExcelOutput:
        return write_excel_workbook(output, {sheet_name: self}, show_table_title)

    def write_excel_sheet(
        self,
        excel_writer: pd.ExcelWriter,
        sheet_name: str = "Montrek Data",
        show_table_title: bool = False,
        frame: pd.DataFrame | None = None,
    ) -> None:
        """Write this manager as one sheet of an already open workbook.

        ``frame`` lets the caller hand in an already built frame, so the
        building happens before the workbook is opened - see
        ``write_excel_workbook``.
        """
        frame = self.get_excel_frame() if frame is None else frame
        row_offset = 3 if show_table_title else 0
        frame.to_excel(
            excel_writer,
            index=False,
            header=self.excel_header,
            sheet_name=sheet_name,
            startrow=row_offset,
        )
        self.disarm_formula_cells(excel_writer.sheets[sheet_name])
        self.get_excel_formatter().format_worksheet(
            excel_writer,
            sheet_name=sheet_name,
            col_formats=self.get_excel_col_formats(),
            table_title=self.table_title if show_table_title else None,
        )

    @staticmethod
    def disarm_formula_cells(worksheet) -> None:
        """Store exported text that looks like a formula as text.

        openpyxl types any string starting with "=" as a formula, and exported
        fields carry text people typed - so a field holding "=..." would be
        executed by whatever spreadsheet opens the file. Retyping the cell
        leaves the text exactly as it was entered, where the usual apostrophe
        prefix would become part of the value.
        """
        for row in worksheet.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"

    def get_excel_frame(self) -> pd.DataFrame:
        raise NotImplementedError(
            f"Implement get_excel_frame for {self.__class__.__name__}"
        )

    def get_excel_col_formats(self) -> dict[int, str | None]:
        return {}

    def get_excel_formatter(self) -> MontrekExcelFormatter:
        """Hook for subclasses that need a formatter carrying report state."""
        return self.excel_formatter_class()
