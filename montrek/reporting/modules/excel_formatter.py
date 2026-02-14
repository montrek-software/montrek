from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter

from baseclasses.templatetags.colors import get_color


class MontrekExcelFormatter:
    # Constants for column width calculation
    MIN_COLUMN_WIDTH = 8
    MAX_COLUMN_WIDTH = 50
    COLUMN_PADDING = 2
    BOLD_FONT_MULTIPLIER = 1.2
    NORMAL_FONT_MULTIPLIER = 1.1

    @staticmethod
    def format_excel(writer, sheet_name="Sheet1"):
        """Format an Excel worksheet with styled headers, alternating rows, and auto-sized columns."""
        worksheet = writer.sheets[sheet_name]

        MontrekExcelFormatter._apply_cell_styles(worksheet)
        MontrekExcelFormatter._adjust_column_widths(worksheet)

    @staticmethod
    def _get_style_objects():
        """Create and return all style objects needed for formatting."""
        primary_light = get_color("primary_light").lstrip("#").upper()
        primary = get_color("primary").lstrip("#").upper()

        return {
            "header_fill": PatternFill(
                start_color=primary, end_color=primary, fill_type="solid"
            ),
            "header_font": Font(color="FFFFFF", bold=True),
            "even_row_fill": PatternFill(
                start_color=primary_light, end_color=primary_light, fill_type="solid"
            ),
            "odd_row_fill": PatternFill(
                start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"
            ),
            "thin_border": Border(bottom=Side(style="thin", color="E0E0E0")),
        }

    @staticmethod
    def _apply_cell_styles(worksheet):
        """Apply styles to all cells in the worksheet."""
        styles = MontrekExcelFormatter._get_style_objects()

        for row_idx, row in enumerate(worksheet.iter_rows(), 1):
            for cell in row:
                if row_idx == 1:
                    MontrekExcelFormatter._style_header_cell(cell, styles)
                else:
                    MontrekExcelFormatter._style_data_cell(cell, row_idx, styles)

    @staticmethod
    def _style_header_cell(cell, styles):
        """Apply styling to a header cell."""
        cell.fill = styles["header_fill"]
        cell.font = styles["header_font"]
        cell.alignment = Alignment(horizontal="left")
        cell.border = styles["thin_border"]

    @staticmethod
    def _style_data_cell(cell, row_idx, styles):
        """Apply styling to a data cell with alternating row colors."""
        # Apply alternating row fill
        cell.fill = (
            styles["even_row_fill"] if row_idx % 2 == 0 else styles["odd_row_fill"]
        )
        cell.border = styles["thin_border"]

        # Format based on cell value type
        if isinstance(cell.value, float):
            cell.number_format = "#,##0.00"
            cell.alignment = Alignment(horizontal="right")
        else:
            cell.alignment = Alignment(horizontal="left")

    @staticmethod
    def _adjust_column_widths(worksheet):
        """Auto-size columns based on content with reasonable bounds."""
        for col in worksheet.columns:
            col_cells = list(col)
            if not col_cells:
                continue

            column_letter = get_column_letter(col_cells[0].column)
            max_width = MontrekExcelFormatter._calculate_column_width(col_cells)
            worksheet.column_dimensions[column_letter].width = max_width

    @staticmethod
    def _calculate_column_width(col_cells):
        """Calculate the optimal width for a column based on its cells."""
        max_length = 0

        for cell in col_cells:
            if cell.value is not None:
                display_length = MontrekExcelFormatter._get_display_length(cell)
                max_length = max(max_length, display_length)

        # Apply bounds and padding
        return min(
            max(
                max_length + MontrekExcelFormatter.COLUMN_PADDING,
                MontrekExcelFormatter.MIN_COLUMN_WIDTH,
            ),
            MontrekExcelFormatter.MAX_COLUMN_WIDTH,
        )

    @staticmethod
    def _get_display_length(cell):
        """Calculate the display length of a cell's content."""
        value = cell.value

        # Get base length based on value type
        if isinstance(value, float):
            base_length = len(f"{value:,.2f}")
        else:
            base_length = len(str(value))

        # Apply font multiplier
        multiplier = (
            MontrekExcelFormatter.BOLD_FONT_MULTIPLIER
            if cell.row == 1
            else MontrekExcelFormatter.NORMAL_FONT_MULTIPLIER
        )

        return base_length * multiplier
