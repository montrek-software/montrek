from typing import Any, Literal, cast

from baseclasses.typing import TableDataType, TableElementsType
from reporting.core.text_converter import HtmlLatexConverter
from reporting.dataclasses import table_elements as te


class LatexTableConverter:
    def __init__(
        self,
        table_title: str,
        table_elements: TableElementsType,
        table: TableDataType,
        rows_per_page: int = 25,
        max_cell_chars: int | None = None,
        long_table: bool = False,
    ) -> None:
        self.table_title = table_title
        self.table_elements = table_elements
        self.table = table
        if rows_per_page < 1:
            raise ValueError("rows_per_page must be >= 1")
        self.rows_per_page = rows_per_page
        # Opt-in sizing for tables with long free-text or list cells: a cell
        # claims at most ``max_cell_chars`` of width (it wraps beyond that), but
        # never less than its longest word, so short columns are not starved by
        # one verbose column.
        self.max_cell_chars = max_cell_chars
        # Opt-in ``longtable`` output: the table breaks across pages wherever
        # it has to and repeats its header, instead of a float per
        # ``rows_per_page`` rows. Needed when row heights vary a lot.
        self.long_table = long_table
        self.column_sizer: dict[int, list[int]] = {}
        # Footnote numbers run on across the whole table, so a note repeated on
        # a later page keeps its number; each page lists the notes marked on it.
        self._footnote_numbers: dict[str, int] = {}
        self._page_footnotes: list[int] = []

    def to_latex(self) -> str:
        if self.long_table:
            return self.to_long_latex()
        table_str = self.get_table_str()
        table_start_str = self.get_table_start_str()
        table_end_str = self.get_table_end_str()

        latex_str = table_start_str
        latex_str += table_str
        latex_str += table_end_str
        return latex_str

    def to_long_latex(self) -> str:
        rows_str = self.get_rows_str()
        column_def_str, column_header_str = self._get_long_column_strs()
        head_str = "\\hline\n" + column_header_str
        head_str += "\\arrayrulecolor{primary}\\hline\\arrayrulecolor{bordercolor}\n"
        latex_str = "\n\\begingroup\n\\montrektablesetup\n"
        latex_str += "\\arrayrulecolor{bordercolor}\n"
        latex_str += f"\\begin{{longtable}}{{{column_def_str}}}\n"
        if self.table_title:
            latex_str += f"\\caption*{{{self.table_title}}}\\\\\n"
        latex_str += head_str + "\\endfirsthead\n"
        latex_str += head_str + "\\endhead\n"
        latex_str += rows_str
        latex_str += "\\end{longtable}\n"
        latex_str += self.get_footnotes_str()
        latex_str += "\\endgroup\n\n"
        return latex_str

    def _get_long_column_strs(self) -> tuple[str, str]:
        """Column spec with explicit widths, and the header row.

        ``longtable`` has no X columns, so the share each column gets from
        ``get_column_sizes`` is turned into an explicit, vertically centred
        ``m`` width of the line.
        """
        column_sizes = self.get_column_sizes()
        n_cols = max(len(column_sizes), 1)
        # The padding is taken off the line before it is shared out, so a
        # narrow column keeps the full width its characters asked for.
        text_width = f"(\\linewidth-{2 * n_cols}\\tabcolsep)"
        column_def_str = ""
        column_header_str = "\\montrektableheadrow "
        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            # \dimexpr only scales by integers, so the share is given in 1/10000.
            share = round(column_sizes.get(col_idx, 0) / n_cols * 10000)
            alignment = table_element.latex_column_alignment or "\\RaggedRight"
            column_def_str += (
                f">{{{alignment}\\arraybackslash}}"
                f"m{{\\dimexpr{text_width}*{share}/10000\\relax}}"
            )
            column_header_str += (
                f"\\montrektableheadcell{{{self._get_header_str(table_element)}}} & "
            )
            col_idx += 1
        return column_def_str, column_header_str[:-2] + "\\\\\n"

    @staticmethod
    def _get_header_str(table_element: te.TableElement) -> str:
        element_header = HtmlLatexConverter.convert(table_element.name)
        return " ".join([f"\\mbox{{{head}}}" for head in element_header.split(" ")])

    def get_table_start_str(self) -> str:
        # Font size, column padding and row height come from \montrektablesetup
        # so that a report's .tex template owns the table look; see
        # latex_templates/montrek_base_template.tex for the defaults.
        table_start_str = "\n\\begin{table}[H]\n\\centering\n\\montrektablesetup\n"
        table_start_str += "\\arrayrulecolor{bordercolor}\n"
        table_start_str += f"\\caption{{{self.table_title}}}\n"
        table_start_str += "\\begin{tabularx}{\\textwidth}{"
        column_def_str = ""
        column_header_str = "\\montrektableheadrow "
        column_sizes = self.get_column_sizes()

        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            column_size = column_sizes.get(col_idx, 0)
            alignment = table_element.latex_column_alignment
            column_def_str += f">{{{alignment}\\hsize={column_size}\\hsize}}X "
            element_header = self._get_header_str(table_element)
            column_header_str += f"\\montrektableheadcell{{{element_header}}} & "
            col_idx += 1
        table_start_str += column_def_str.rstrip()
        table_start_str += "}\n\\hline\n"
        table_start_str += column_header_str[:-2] + "\\\\\n"
        table_start_str += (
            "\\arrayrulecolor{primary}\\hline\\arrayrulecolor{bordercolor}\n"
        )
        return table_start_str

    def get_table_end_str(self) -> str:
        table_end_str = "\\end{tabularx}\n"
        table_end_str += self.get_footnotes_str()
        table_end_str += "\\end{table}\n\n"
        return table_end_str

    def get_footnotes_str(self) -> str:
        """The notes marked on the current page, then start a fresh page.

        Printed inside the table float, directly below the tabular, rather than
        as page footnotes: ``\\footnote`` does not work inside a tabular, and
        the notes belong with the table even when it floats.
        """
        if not self._page_footnotes:
            return ""
        texts = {number: text for text, number in self._footnote_numbers.items()}
        notes = ""
        for number in self._page_footnotes:
            text = HtmlLatexConverter.convert(texts[number])
            notes += f"\\montrektablenote{{{number}}}{{{text}}}"
        self._page_footnotes = []
        return f"\\montrektablenotes{{{notes}}}\n"

    def _add_footnote_mark(self, cell_str: str, footnote: str) -> str:
        """Put the note's number behind the cell's value.

        Every element's LaTeX ends in the column separator ``&``, so the mark
        goes right before it.
        """
        number = self._footnote_numbers.setdefault(
            footnote, len(self._footnote_numbers) + 1
        )
        if number not in self._page_footnotes:
            self._page_footnotes.append(number)
        separator_idx = cell_str.rfind("&")
        return (
            f"{cell_str[:separator_idx].rstrip()}"
            f"\\montrektablenotemark{{{number}}} {cell_str[separator_idx:]}"
        )

    def get_rows_str(self) -> str:
        self._seed_column_sizer_from_headers()
        return "".join(self._get_row_str(query_object) for query_object in self.table)

    def _get_row_str(self, query_object: Any) -> str:
        row_str = ""
        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            self.add_to_column_sizer(table_element, query_object, col_idx)
            # The latex tag always renders a string.
            cell_str = cast(str, table_element.get_attribute(query_object, "latex"))
            footnote = table_element.get_footnote(query_object)
            if footnote:
                cell_str = self._add_footnote_mark(cell_str, footnote)
            row_str += cell_str
            col_idx += 1
        return row_str[:-2] + "\\\\\n\\hline\n"

    def get_table_str(self) -> str:
        table_str = ""
        self._seed_column_sizer_from_headers()
        table_len = len(self.table)

        for i, query_object in enumerate(self.table):
            table_str += self._get_row_str(query_object)
            if (i + 1) % self.rows_per_page == 0 and (i + 1) != table_len:
                table_str += self.get_table_end_str()
                table_str += "\\newpage\n"
                table_str += self.get_table_start_str()
        return table_str

    def _seed_column_sizer_from_headers(self) -> None:
        col_idx = 0
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            header_width = self._header_width(table_element.name)
            if self.max_cell_chars is not None:
                # Capped sizing keeps columns close to their content, so the
                # bold header words need their extra weight accounted for.
                header_width += 2
            self.column_sizer[col_idx] = [header_width]
            col_idx += 1

    @staticmethod
    def _header_width(name: str) -> int:
        """Width a header demands, in characters.

        Header words are set in individual \\mbox es, so the header wraps
        between them and only needs to fit its longest word. Charging the
        column for the full header instead starves the data columns next to a
        verbose header such as "gestres. Limit Auslastung".
        """
        words = str(name).split()
        return max((len(word) for word in words), default=0)

    def add_to_column_sizer(
        self, table_element: te.TableElement, query_object: Any, col_idx: int
    ):
        value_len = table_element.get_value_len(query_object)
        if self.max_cell_chars is not None:
            value_len = self._capped_value_len(table_element, query_object, value_len)
        if col_idx not in self.column_sizer:
            self.column_sizer[col_idx] = [value_len]
        else:
            self.column_sizer[col_idx].append(value_len)

    def _capped_value_len(
        self, table_element: te.TableElement, query_object: Any, value_len: int
    ) -> int:
        if not table_element.latex_wraps:
            # Unbreakable cells (bold text in a \colorbox) also need room for
            # the box padding and the heavier weight.
            return value_len + 2
        value = table_element.get_value(query_object)
        if isinstance(value, list | tuple):
            value = ", ".join(str(item) for item in value)
        longest_word = max((len(word) for word in str(value).split()), default=0)
        return max(min(value_len, cast(int, self.max_cell_chars)), longest_word)

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
