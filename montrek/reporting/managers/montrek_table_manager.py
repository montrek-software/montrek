import datetime
import math
import tempfile
import uuid
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from collections.abc import Callable, Mapping
from typing import Any, ClassVar

import pandas as pd
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.typing import SessionDataType, TableDataType, TableElementsType
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils import timezone
from django_pandas.io import read_frame
from mailing.managers.mailing_manager import MailingManager
from reporting.core import reporting_text as rt
from reporting.core.table_converter import LatexTableConverter
from reporting.core.text_converter import HtmlTextConverter
from reporting.dataclasses import table_elements as te
from reporting.dataclasses.display_field import DisplayField
from reporting.dataclasses.summary_row_config import SummaryRowConfig
from reporting.lib.protocols import ReportElementProtocol
from reporting.managers.excel_export import ExcelSheetMixin
from reporting.modules.data_frame_filter import DataFrameFilter
from reporting.modules.mailed_downloads import MailedDownloads
from reporting.modules.summary_row import SummaryRow
from reporting.modules.excel_formatter import MontrekExcelFormatter
from reporting.modules.table_serializer import TableSerializer
from reporting.tasks.download_table_task import DownloadTableTask
from reporting.tasks.refresh_data_task import RefreshDataTask


class MontrekTableMetaClass(type):
    def __init__(cls, name, bases, dct):
        if getattr(cls, "show_summary_row", False) and getattr(cls, "is_large", False):
            raise ImproperlyConfigured(
                f"{name} is large and cannot show a summary row: the sums would "
                "read all rows of the table."
            )
        cls.download_task = DownloadTableTask(manager_class=cls)
        cls.refresh_data_task = RefreshDataTask(manager_class=cls)
        super().__init__(name, bases, dct)


class MontrekTableManagerABC(
    ExcelSheetMixin, MontrekManager, metaclass=MontrekTableMetaClass
):
    table_title = ""
    document_title = "Montrek Table"
    draft = False
    is_compact_format = False
    has_table_elements_filter_field: bool = True
    is_large: bool = False
    # A row under the table with the sum of each numeric column over all rows
    show_summary_row: bool = False
    summary_row_config: ClassVar[SummaryRowConfig] = SummaryRowConfig()
    latex_rows_per_page: int = 25
    # See LatexTableConverter: cap on a cell's claim to column width, and
    # page-breaking longtable output instead of fixed-size table floats.
    latex_max_cell_chars: int | None = None
    latex_long_table: bool = False
    excel_formatter_class: type[MontrekExcelFormatter] = MontrekExcelFormatter
    # Manager whose table elements (and repository) back the CSV, Excel and JSON
    # exports when they need more than the on-screen table shows.
    export_manager_class: ClassVar[type["MontrekTableManagerABC"] | None] = None
    # Set on first use by ``get_display_field_names``; class level so subclasses
    # with their own ``__init__`` signature cannot miss it.
    _table_element_field_names: dict[str, str] | None = None
    # Path of the list view showing the table, which refreshes single rows for
    # live table elements; empty where no view does. Set by that view.
    live_rows_path: str = ""
    # Set per subclass by ``MontrekTableMetaClass``.
    download_task: ClassVar[DownloadTableTask]
    refresh_data_task: ClassVar[RefreshDataTask]

    def __init__(self, session_data: SessionDataType | None = None):
        super().__init__(session_data)
        self._document_name: None | str = None
        self._queryset: None | TableDataType = None
        self.is_current_compact_format: bool = self.get_is_compact_format()
        self.order_descending = False
        self.order_field: None | str = self.get_order_field()

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    @property
    def table_elements(self) -> TableElementsType:
        return ()

    @cached_property
    def export_manager(self) -> "MontrekTableManagerABC":
        if self.export_manager_class is None:
            return self
        export_manager = self.export_manager_class(self.session_data)
        # Shared, so messages raised during an export reach the view.
        export_manager.messages = self.messages
        return export_manager

    @property
    def document_name(self) -> str:
        if not self._document_name:
            manager_name = self.__class__.__name__.lower()
            self._document_name = (
                f"{manager_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
        return self._document_name

    def get_is_compact_format(self) -> bool:
        return self.session_data.get(
            "current_is_compact_format", self.is_compact_format
        )

    def get_order_field(self) -> None | str:
        order_field = self.session_data.get("order_field", None)
        if isinstance(order_field, list | tuple):
            order_field = order_field[0]
        if order_field is None:
            return None
        if len(order_field) > 0 and order_field[0] == "-":
            self.order_descending = True
        return order_field

    def set_order_field(self):
        if self.order_field:
            self.repository.set_order_fields((str(self.order_field),))

    def get_table(self) -> TableDataType:
        raise NotImplementedError("Method get_table must be implemented")

    def get_full_table(self) -> TableDataType:
        raise NotImplementedError("Method get_full_table must be implemented")

    def get_df(self) -> pd.DataFrame:
        raise NotImplementedError("Method get_df must be implemented")

    def _get_table_dimensions(self) -> int:
        raise NotImplementedError("Method _get_table_dimensions must be implemented")

    def get_table_elements_name_to_field_map(self) -> dict[str, str]:
        name_to_field_map = {}
        for element in self.table_elements:
            te_field = (
                "text" if isinstance(element, te.LinkTextTableElement) else "attr"
            )
            name_to_field_map[element.name] = getattr(element, te_field, "")
        return name_to_field_map

    def get_field_table_elements_name_map(self) -> dict[str, str]:
        return {
            ele.attr: ele.name for ele in self.table_elements if hasattr(ele, "attr")
        }

    def get_display_fields(
        self, table_elements: TableElementsType | None = None
    ) -> list[list[DisplayField]]:
        # Resolve table_elements once: the property may build per-table state
        # (caches, containers), which is lost when re-read for every row.
        if table_elements is None:
            table_elements = self.table_elements
        return [
            [element.get_display_field(query_object) for element in table_elements]
            for query_object in self.get_table()
        ]

    def get_table_headers(
        self, table_elements: TableElementsType
    ) -> list[tuple[te.TableElement, str]]:
        """Each table element paired with the help text of its field."""
        help_texts = self.get_field_help_texts()
        return [
            (element, help_texts.get(element.field_name, ""))
            for element in table_elements
        ]

    def to_html(self):
        template = get_template("tables/base_table.html")
        if self.order_descending and self.order_field is not None:
            order_field = self.order_field[1:]
        else:
            order_field = self.order_field
        table_elements = self.table_elements
        display_fields = self.get_display_fields(table_elements)
        return template.render(
            context={
                "table_title": self.table_title,
                "table_headers": self.get_table_headers(table_elements),
                "display_fields": display_fields,
                "summary_fields": self._get_summary_fields_if_rows(
                    table_elements, display_fields
                ),
                "order_field": order_field,
                "order_descending": self.order_descending,
            }
        )

    def get_summary_fields(
        self, table_elements: TableElementsType
    ) -> list[DisplayField] | None:
        """The cells of the summary row, or None without one."""
        summary = self._get_summary(table_elements)
        if summary is None:
            return None
        summary_row, sums = summary
        return summary_row.display_fields(sums)

    def _get_summary(
        self, table_elements: TableElementsType
    ) -> tuple[SummaryRow, list[Any]] | None:
        if not self.show_summary_row:
            return None
        summary_row = SummaryRow(self.summary_row_config, table_elements)
        return summary_row, self.get_column_sums(summary_row.summed_elements)

    def get_column_sums(self, elements: list[te.NumberTableElement]) -> list[Any]:
        """The sum of each element over all rows of the table, not only the
        page, in the order of the elements."""
        try:
            table = self.get_full_table()
        except NotImplementedError:
            table = self.get_table()
        return SummaryRow.sum_rows(table, elements)

    def _get_summary_fields_if_rows(
        self, table_elements: TableElementsType, display_fields: list
    ) -> list[DisplayField] | None:
        if not display_fields:
            return None
        return self.get_summary_fields(table_elements)

    def render_single_row(self, query_object) -> str:
        """Render a single ``<tr>`` using the same markup as the full table.

        Used for HTMX swaps that replace one table row in place (``hx-target``
        ``closest tr``, ``hx-swap`` ``outerHTML``) without re-rendering (or
        re-querying) the whole report.
        """
        cells = [
            table_element.get_display_field(query_object)
            for table_element in self.table_elements
        ]
        return render_to_string("tables/partials/table_row.html", {"cells": cells})

    def get_table_row(self, _row_id: int) -> Any | None:
        """The row ``row_id`` of the full table, or None if it is not in it.

        Backs the row refreshes of live table elements; tables that cannot
        look up a single row answer None and the refreshes stop.
        """
        return None

    def get_all_fields(self) -> list[str]:
        if not self.has_table_elements_filter_field:
            return super().get_all_fields()
        return list(self.get_display_field_names())

    def get_display_field_names(self) -> Mapping[str, str]:
        """Filterable field -> column header, derived from the table elements.

        Cached: ``table_elements`` may build per-table state and is read by both
        this method and ``get_all_fields``, which the field choices need together.
        """
        if not self.has_table_elements_filter_field:
            return super().get_display_field_names()
        if self._table_element_field_names is None:
            # Elements without a queryset field (icon links) are not filterable.
            self._table_element_field_names = {
                field_name: element.name
                for element in self.table_elements
                if (field_name := element.field_name)
            }
        return self._table_element_field_names

    def get_all_display_fields(self) -> list[list[DisplayField]]:
        """All rows (unpaginated) for PDF rendering."""
        try:
            table = self.get_full_table()
        except NotImplementedError:
            table = self.get_table()
        pdf_elements = [
            e for e in self.table_elements if not isinstance(e, te.LinkTableElement)
        ]
        return [[e.get_display_field(obj) for e in pdf_elements] for obj in table]

    def to_pdf_html(self) -> str:
        template = get_template("tables/base_table.html")
        pdf_elements = [
            e for e in self.table_elements if not isinstance(e, te.LinkTableElement)
        ]
        display_fields = self.get_all_display_fields()
        return template.render(
            context={
                "table_title": self.table_title,
                "table_headers": self.get_table_headers(pdf_elements),
                "display_fields": display_fields,
                "summary_fields": self._get_summary_fields_if_rows(
                    pdf_elements, display_fields
                ),
                "order_field": None,
                "order_descending": False,
                "pdf_mode": True,
            }
        )

    def to_json(self) -> list[dict]:
        export_manager = self.export_manager
        serializer = TableSerializer(export_manager.table_elements)
        return serializer.serialize_all(export_manager.get_full_table())

    def to_latex(self):
        table_elements = self.table_elements
        table = self.get_full_table()
        summary = (
            self._get_summary(self._get_export_elements(table_elements))
            if len(table)
            else None
        )
        return LatexTableConverter(
            self.table_title,
            table_elements,
            table,
            rows_per_page=self.latex_rows_per_page,
            max_cell_chars=self.latex_max_cell_chars,
            long_table=self.latex_long_table,
            summary_cells=(
                None if summary is None else summary[0].latex_cells(summary[1])
            ),
        ).to_latex()

    def get_excel_frame(self) -> pd.DataFrame:
        """The sheet's rows, and the summary row under them. CSV and JSON
        leave it out: programs reading them would count it as a row."""
        frame = self.get_output_df()
        summary = (
            None
            if frame.empty
            else self._get_summary(self._get_export_elements(self.table_elements))
        )
        if summary is None:
            return frame
        summary_row, sums = summary
        values = summary_row.excel_values(sums)
        frame = frame.copy()
        frame.loc[len(frame)] = [values.get(column) for column in frame.columns]
        return frame

    @staticmethod
    def _get_export_elements(
        table_elements: TableElementsType,
    ) -> list[te.TableElement]:
        """The columns LaTeX and Excel write: without the link columns, so
        that the summary row's label lands in one of them."""
        return [
            element
            for element in table_elements
            if not isinstance(element, te.LinkTableElement)
        ]

    def get_excel_formatter(self) -> MontrekExcelFormatter:
        formatter = super().get_excel_formatter()
        formatter.summary_row = self.show_summary_row
        return formatter

    def get_excel_col_formats(self) -> dict[int, str | None]:
        elements = [
            e for e in self.table_elements if not isinstance(e, te.LinkTableElement)
        ]
        return {idx: e.excel_format_str for idx, e in enumerate(elements)}

    def to_csv(self, output: HttpResponse | str) -> HttpResponse | str:
        table_df = self.get_output_df()
        table_df.to_csv(output, index=False)
        return output

    def get_output_df(self) -> pd.DataFrame:
        return self.get_df()

    def download_or_mail_csv(self) -> HttpResponse:
        export_manager = self.export_manager
        return export_manager._download_or_mail("csv", export_manager._download_csv)

    def download_or_mail_excel(self) -> HttpResponse:
        export_manager = self.export_manager
        return export_manager._download_or_mail("xlsx", export_manager._download_excel)

    def _download_or_mail(
        self, filetype: str, download_method: Callable[[], HttpResponse]
    ) -> HttpResponse:
        if self.is_large:
            return self._handle_large_table(filetype)
        table_dimensions = self._get_table_dimensions()
        if table_dimensions > settings.SEND_TABLE_BY_MAIL_LIMIT:
            return self._handle_large_table(filetype)
        return download_method()

    def _handle_large_table(self, filetype: str) -> HttpResponse:
        self.messages.append(
            MontrekMessageInfo("Table is too large to download. Sending it by mail.")
        )
        self.download_task.delay(filetype=filetype, session_data=self.session_data)
        request_path = self.session_data.get("request_path", "")
        return HttpResponseRedirect(request_path)

    def _download_excel(self):
        response = HttpResponse()
        self.to_excel(response)
        response = self.do_download(
            response=response,
            filename=f"{self.document_name}.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return response

    def _download_csv(self):
        response = HttpResponse()
        self.to_csv(response)
        response = self.do_download(
            response=response,
            filename=f"{self.document_name}.csv",
            content_type="text/csv",
        )
        return response

    def do_download(self, response, filename, content_type):
        response["Content-Type"] = content_type
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _make_datetime_naive(self, value):
        if isinstance(value, datetime.datetime) and not timezone.is_naive(value):
            value = timezone.make_naive(value)
        return value

    def _make_float(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def send_table_by_mail(self, filetype: str):
        file_name = MailedDownloads.file_name_for_link(
            f"{self.document_name}.{filetype}"
        )
        # A disk-backed file, not a string: these are the tables too large
        # for a direct download, and the CSV would otherwise be held in
        # memory twice, as text and as bytes.
        with tempfile.TemporaryFile() as output:
            if filetype == "xlsx":
                self.to_excel(output)
            elif filetype == "csv":
                self.get_output_df().to_csv(output, index=False)
            else:
                return
            output.seek(0)
            download_id = MailedDownloads(self.session_data["user_id"]).store(
                file_name, File(output, file_name)
            )
        self._send_mail_with_file(download_id, file_name)

    def _send_mail_with_file(self, download_id: uuid.UUID, file_name: str):
        file_url = self.session_data.get("host_url", "/") + reverse(
            "download_reporting_file",
            kwargs={"download_id": download_id, "file_name": file_name},
        )
        mailing_manager = MailingManager(self.session_data)
        message = "".join(
            (
                "Please download the table from the link below:<br>",
                f"<a href='{file_url}'>{file_name}</a><br>",
                "<i>Link will be invalid after first download</i>",
            )
        )
        mailing_manager.send_montrek_mail_to_user(
            subject=f"{file_name} is ready for download",
            message=message,
        )


@dataclass
class MontrekTablePaginator:
    number: int
    num_pages: int
    show_paginator: bool

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.num_pages or self.num_pages == -1

    @property
    def previous_page_number(self) -> int:
        return self.number - 1

    @property
    def next_page_number(self) -> int:
        return self.number + 1


class MontrekTableManager(MontrekTableManagerABC):
    is_paginated = True

    def __init__(self, session_data: SessionDataType | None = None):
        super().__init__(session_data)
        self.paginator: None | MontrekTablePaginator = None
        self.paginate_by: int = self.get_paginate_by()

    def get_paginate_by(self):
        paginate_by = self.session_data.get("current_paginate_by", 10)
        return max(paginate_by, 5)

    def get_table(self) -> TableDataType:
        queryset = self._get_queryset(self.get_paginated_queryset)
        self._preload_container(queryset)
        return queryset

    def get_full_table(self) -> QuerySet:
        self.set_order_field()
        return self.repository.receive()

    def get_column_sums(self, elements: list[te.NumberTableElement]) -> list[Any]:
        """Summed in SQL where the sum of the column is the sum of the values
        the element shows; otherwise in Python over all rows."""
        queryset = self.get_full_table()
        if not isinstance(queryset, QuerySet):
            return super().get_column_sums(elements)
        sql_sums = self.repository.get_column_sums(
            queryset,
            [
                element.attr
                for element in elements
                if self._is_summed_in_sql(queryset, element)
            ],
        )
        totals: list[Any] = [None] * len(elements)
        python_indexes = []
        for index, element in enumerate(elements):
            if self._is_summed_in_sql(queryset, element) and element.attr in sql_sums:
                totals[index] = sql_sums[element.attr]
            else:
                python_indexes.append(index)
        if python_indexes:
            rows = list(queryset)
            self._preload_container(rows)
            python_sums = SummaryRow.sum_rows(
                rows, [elements[index] for index in python_indexes]
            )
            for index, total in zip(python_indexes, python_sums, strict=True):
                totals[index] = total
        return totals

    def _is_summed_in_sql(
        self, queryset: QuerySet, element: te.NumberTableElement
    ) -> bool:
        if type(element).get_value is not te.NumberTableElement.get_value:
            return False
        if element.numerical_type is float:
            return True
        # Values shown as integers are truncated one by one, which the sum of
        # a float or decimal column is not
        if element.numerical_type is int:
            return self.repository.is_integer_column(queryset, element.attr)
        return False

    def get_table_row(self, row_id: int) -> Any | None:
        rows = list(self.get_full_table().filter(pk=row_id)[:1])
        self._preload_container(rows)
        return rows[0] if rows else None

    def get_df(self) -> pd.DataFrame:
        queryset = self.repository.receive()
        self._preload_container(queryset)
        queryset = list(queryset)
        return self._build_df(queryset)

    def _preload_container(self, queryset: TableDataType) -> None:
        """Hook for subclasses to bulk-prefetch data before row iteration."""

    def _build_df(self, queryset: list) -> pd.DataFrame:
        table_data = {}
        table_elements = [
            table_element
            for table_element in self.table_elements
            if not isinstance(table_element, te.LinkTableElement)
        ]
        for element in table_elements:
            table_data[element.name] = [
                HtmlTextConverter.convert(element.get_value(row)) for row in queryset
            ]
        return pd.DataFrame(table_data)

    def get_paginated_queryset(self) -> TableDataType:
        queryset = self.get_full_table()
        if self.is_paginated:
            return self._paginate_queryset(queryset)
        return queryset

    def _paginate_queryset(self, queryset: QuerySet) -> list:
        page_number = int(self.session_data.get("page", [1])[0])
        paginate_by = self.paginate_by
        offset = (page_number - 1) * paginate_by
        results = list(
            queryset[offset : offset + paginate_by + 1]
        )  # Fetch 1 extra item

        len_results = len(results)
        trim_next = len_results > paginate_by
        if trim_next:
            results = results[:paginate_by]
        len_full_table = (
            paginate_by + 5 if self.is_large else self.get_full_table().count()
        )
        show_paginator = len_full_table > paginate_by
        num_pages = -1 if self.is_large else math.ceil(len_full_table / paginate_by)

        self.paginator = MontrekTablePaginator(
            number=page_number,
            num_pages=num_pages,
            show_paginator=show_paginator,
        )
        return results

    def _get_table_dimensions(self) -> int:
        rows = self.repository.receive().count()
        cols = len(self.table_elements)
        return rows * cols

    def _get_queryset(self, func: Callable[[], TableDataType]) -> TableDataType:
        if self._queryset:
            return self._queryset
        queryset = func()
        self._queryset = queryset
        return queryset


class MontrekDataFrameTableManager(MontrekTableManagerABC):
    is_paginated = False

    def __init__(self, session_data: SessionDataType | None = None):
        session_data = {} if session_data is None else session_data
        if "df_data" not in session_data:
            raise ValueError("DataFrame data not set in session_data['df_data'].")
        self.df_data = session_data["df_data"]
        self.df = self.set_df()
        super().__init__(session_data)
        self.paginator: None | MontrekTablePaginator = None
        self.paginate_by: int = self.get_paginate_by()
        self._apply_filter()

    def get_paginate_by(self) -> int:
        paginate_by = self.session_data.get("current_paginate_by", 10)
        return max(paginate_by, 5)

    @staticmethod
    def get_source_session_data(session_data: SessionDataType) -> SessionDataType:
        """Session data for the managers and repositories that build the rows.

        Without the filter of the view: it applies to the rows of this table,
        and a repository given it would apply it to its own fields instead."""
        return {key: value for key, value in session_data.items() if key != "filter"}

    def _apply_filter(self) -> None:
        """Applies the filter of the list view to the rows, so that the table,
        its summary row and the exports show the same rows.

        The rows are kept as given rather than rebuilt from the DataFrame, which
        would turn None into NaN and dates into Timestamps. A filter that
        cannot be applied yields no rows, as on a queryset."""
        request_path = self.session_data.get("request_path", "")
        filter_dict = self.session_data.get("filter", {}).get(request_path, {})
        # Rows without values have no columns to check the filter against
        if not filter_dict or not self.df_data:
            return
        try:
            mask = DataFrameFilter(filter_dict).mask(self.df).to_numpy()
        except (ValueError, TypeError) as e:
            message = MontrekMessageError(f"Filter could not be applied: {e}")
            if message not in self.messages:
                self.messages.append(message)
            mask = [False] * len(self.df_data)
        self.df_data = [
            row for row, keep in zip(self.df_data, mask, strict=True) if keep
        ]
        self.df = self.df[mask]

    def get_table(self) -> list[dict]:
        full_table = self.get_full_table()
        if self.is_paginated:
            return self._paginate_table(full_table)
        return full_table

    def get_full_table(self) -> list[dict]:
        return self.df_data

    def _paginate_table(self, full_table: list) -> list:
        page_number = int(self.session_data.get("page", [1])[0])
        paginate_by = self.paginate_by
        offset = (page_number - 1) * paginate_by
        len_full_table = len(full_table)

        self.paginator = MontrekTablePaginator(
            number=page_number,
            num_pages=math.ceil(len_full_table / paginate_by),
            show_paginator=len_full_table > paginate_by,
        )
        return full_table[offset : offset + paginate_by]

    def set_df(self):
        return pd.DataFrame(self.df_data)

    def get_excel_col_formats(self) -> dict[int, str | None]:
        """By the column of the data each element shows: the sheet holds all
        columns of the data, not only those of the table, and two columns may
        share a header. ``get_df`` keeps the order of the columns."""
        formats = {
            element.attr: element.excel_format_str
            for element in self.table_elements
            if isinstance(element, te.AttrTableElement)
        }
        return {
            index: formats.get(column) for index, column in enumerate(self.df.columns)
        }

    def get_df(self) -> pd.DataFrame:
        return self.df.rename(columns=self.get_field_table_elements_name_map())

    def _get_table_dimensions(self) -> int:
        return self.df.shape[0] * self.df.shape[1]

    def download(self) -> HttpResponse:
        return self.to_excel(HttpResponse())


EXCLUDE_COLUMNS = [
    "id",
    "created_at",
    "updated_at",
    "hash_identifier",
    "hash_value",
    "hub_entity",
    "hub_value_date",
]


class HistoryDataTableManager(MontrekTableManagerABC):
    is_current_compact_format = True
    order_field = "-created_at"

    def __init__(self, session_data: SessionDataType, title: str, queryset: QuerySet):
        super().__init__(session_data)
        self.title = title
        self.queryset = queryset
        self.change_map = self.get_change_map()
        self.table = self.to_html()

    def get_table(self) -> TableDataType:
        return self.queryset

    @property
    def table_elements(self) -> list[te.TableElement]:
        columns = self.queryset.model._meta.fields
        elements: list[te.TableElement] = []
        for column in columns:
            if column.name in EXCLUDE_COLUMNS:
                continue
            elements.append(
                te.HistoryStringTableElement(
                    attr=column.name, name=column.name, change_map=self.change_map
                )
            )
        return elements

    def get_change_map(self) -> te.ChangeMapType:
        sat_df = read_frame(self.queryset)
        return self.get_change_map_from_df(sat_df)

    @staticmethod
    def get_change_map_from_df(df: pd.DataFrame) -> te.ChangeMapType:
        is_timeseries = "value_date" in df.columns
        id_column = "id"

        exclude_cols = [id_column, "state_date_start", "state_date_end", "value_date"]
        # Make a copy of the dataframe sorted by id in descending order (bottom to top)
        sort_col = "value_date" if is_timeseries else id_column
        sorted_df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
        changes: te.ChangeMapType = {}

        # Iterate through rows from bottom to top (highest id to lowest)
        for i in range(len(sorted_df) - 1):
            current_row = sorted_df.iloc[i]
            next_row = sorted_df.iloc[i + 1]

            current_id = current_row[id_column]
            next_id = next_row[id_column]

            if is_timeseries and current_row["value_date"] != next_row["value_date"]:
                continue
            # Compare all columns except the id column
            for col in sorted_df.columns:
                if col not in exclude_cols and current_row[col] != next_row[col]:
                    # If there's a change, record it
                    if current_id not in changes:
                        changes[int(current_id)] = {}
                    if next_id not in changes:
                        changes[int(next_id)] = {}

                    changes[int(current_id)][col] = te.HistoryChangeState.NEW
                    changes[int(next_id)][col] = te.HistoryChangeState.OLD
        return changes
