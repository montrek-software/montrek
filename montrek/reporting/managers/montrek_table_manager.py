import datetime
import os
from io import BytesIO
from typing import Any
from django.db.models import QuerySet

import pandas as pd
from baseclasses.dataclasses.montrek_message import MontrekMessageInfo
from baseclasses.managers.montrek_manager import MontrekManager
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import HttpResponse
from mailing.managers.mailing_manager import MailingManager
from reporting.core import reporting_text as rt
from reporting.dataclasses import table_elements as te
from reporting.lib.protocols import (
    ReportElementProtocol,
)
from reporting.tasks.download_table_task import DownloadTableTask


class MontrekTableMetaClass(type):
    def __init__(cls, name, bases, dct):
        cls.download_task = DownloadTableTask(manager_class=cls)
        super().__init__(name, bases, dct)


class MontrekTableManagerABC(MontrekManager, metaclass=MontrekTableMetaClass):
    table_title = ""
    document_title = "Montrek Table"
    draft = False

    def __init__(self, session_data: dict[str, Any] = {}):
        super().__init__(session_data)
        self._document_name: None | str = None

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return ()

    @property
    def document_name(self) -> str:
        if not self._document_name:
            repo_name = self.repository.__class__.__name__.lower()
            self._document_name = (
                f"{repo_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
        return self._document_name

    def get_table(self) -> QuerySet | dict:
        raise NotImplementedError("Method get_table must be implemented")

    def get_full_table(self) -> QuerySet | dict:
        raise NotImplementedError("Method get_full_table must be implemented")

    def get_df(self) -> pd.DataFrame:
        raise NotImplementedError("Method get_df must be implemented")

    def get_table_elements_name_to_field_map(self) -> dict[str, str]:
        name_to_field_map = {}
        for element in self.table_elements:
            name_to_field_map[element.name] = getattr(element, "attr", "")
        return name_to_field_map

    def to_html(self):
        html_str = f"<h3>{self.table_title}</h3>"
        html_str += '<table class="table table-bordered table-hover"><tr>'
        for table_element in self.table_elements:
            html_str += f"<th title={getattr(table_element, 'attr', '')}>{table_element.name}</th>"
        html_str += "</tr>"
        table = self.get_table()
        for query_object in table:
            html_str += '<tr style="white-space:nowrap;">'
            for table_element in self.table_elements:
                html_str += table_element.get_attribute(query_object, "html")
            html_str += "</tr>"
        html_str += "</table>"
        return html_str

    def to_latex(self):
        table_start_str = "\n\\begin{table}[H]\n\\centering\n"
        table_start_str += "\\arrayrulecolor{lightgrey}\n"
        table_start_str += "\\setlength{\\tabcolsep}{2pt}\n"
        table_start_str += "\\renewcommand{\\arraystretch}{1.0}\n"
        table_start_str += f"\\caption{{{self.table_title}}}\n"
        table_start_str += "\\begin{tabularx}{\\textwidth}{|"
        table_end_str = "\\end{tabularx}\n\\end{table}\n\n"

        column_def_str = ""
        column_header_str = "\\rowcolor{blue}"

        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            column_def_str += "X|"
            column_header_str += f"\\color{{white}}\\textbf{{{table_element.name}}} & "
        table_start_str += column_def_str
        table_start_str += "}\n\\hline\n"
        table_start_str += column_header_str[:-2] + "\\\\\n\\hline\n"
        latex_str = table_start_str

        table = self.get_full_table()
        for i, query_object in enumerate(table):
            if i % 2 == 0:
                latex_str += "\\rowcolor{lightblue}"
            for table_element in self.table_elements:
                if isinstance(table_element, te.LinkTableElement):
                    continue
                latex_str += table_element.get_attribute(query_object, "latex")
            latex_str = latex_str[:-2] + "\\\\\n\\hline\n"
            if (i + 1) % 25 == 0:
                latex_str += table_end_str
                latex_str += table_start_str
        latex_str += table_end_str
        return latex_str

    def to_excel(
        self, output: HttpResponse | BytesIO | str
    ) -> HttpResponse | BytesIO | str:
        table_df = self.get_df()
        with pd.ExcelWriter(output) as excel_writer:
            table_df.to_excel(excel_writer, index=False)
        return output

    def to_csv(self, output: HttpResponse | str) -> HttpResponse | str:
        table_df = self.get_df()
        table_df.to_csv(output, index=False)
        return output

    def download_or_mail_csv(self) -> HttpResponse:
        table_dimensions = self._get_table_dimensions()
        if table_dimensions > settings.SEND_TABLE_BY_MAIL_LIMIT:
            return self._handle_large_table("csv")
        else:
            return self._download_csv()

    def download_or_mail_excel(self) -> HttpResponse:
        table_dimensions = self._get_table_dimensions()
        if table_dimensions > settings.SEND_TABLE_BY_MAIL_LIMIT:
            return self._handle_large_table("xlsx")
        else:
            return self._download_excel()

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

    def _get_table_dimensions(self) -> int:
        rows = self.repository.receive().count()
        cols = len(self.table_elements)
        return rows * cols

    def send_table_by_mail(self, filetype: str):
        file_name = f"{self.document_name}.{filetype}"
        if filetype == "xlsx":
            self._send_table_excel_by_mail(file_name)
        elif filetype == "csv":
            self._send_table_csv_by_mail(file_name)

    def _send_table_excel_by_mail(self, file_name: str):
        output = BytesIO()
        self.to_excel(output)
        output.seek(0)
        file_name = f"{self.document_name}.xlsx"
        temp_file_path = os.path.join("temp", file_name)

        # Save the file to the default storage (e.g., file system or cloud storage)
        saved_file = default_storage.save(temp_file_path, ContentFile(output.read()))
        self._send_mail_with_file(saved_file, file_name)

    def _send_table_csv_by_mail(self, file_name: str):
        temp_file_path = os.path.join(file_name)
        self.to_csv(default_storage.path(temp_file_path))
        self._send_mail_with_file(temp_file_path, file_name)

    def _send_mail_with_file(self, saved_file: str, file_name: str):
        # Return the URL of the stored file
        file_url = self.session_data.get("host_url", "/") + reverse(
            "download_reporting_file", kwargs={"file_path": saved_file}
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


class MontrekTableManager(MontrekTableManagerABC):
    is_paginated = True
    paginate_by = 10

    def get_table(self) -> QuerySet | dict:
        return self.get_paginated_queryset()

    def get_full_table(self) -> QuerySet | dict:
        return self.repository.receive()

    def get_df(self) -> pd.DataFrame:
        queryset = self.repository.receive()
        table_data = {}
        table_elements = [
            table_element
            for table_element in self.table_elements
            if not isinstance(table_element, te.LinkTableElement)
        ]
        for element in table_elements:
            values = []
            for row in queryset.all():
                if hasattr(element, "attr"):
                    attr = getattr(row, element.attr)
                    attr = self._make_datetime_naive(attr)

                    values.append(attr)
                else:
                    values.append(getattr(row, element.text))
            table_data[element.name] = values
        return pd.DataFrame(table_data)

    def get_paginated_queryset(self) -> QuerySet:
        queryset = self.get_full_table()
        if self.is_paginated:
            return self._paginate_queryset(queryset)
        return queryset

    def _paginate_queryset(self, queryset):
        page_number = self.session_data.get("page", [1])[0]
        paginator = Paginator(queryset, self.paginate_by)
        page = paginator.get_page(page_number)
        return page
