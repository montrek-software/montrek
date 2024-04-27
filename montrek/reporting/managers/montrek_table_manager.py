from django.views.generic.base import HttpResponse
from django.core.paginator import Paginator
from baseclasses.managers.montrek_manager import MontrekManager
from reporting.dataclasses import table_elements as te
import csv


class MontrekTableManager(MontrekManager):
    is_paginated = True
    paginate_by = 10

    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return ()

    def to_html(self):
        html_str = '<table class="table table-bordered table-hover"><tr>'
        for table_element in self.table_elements:
            html_str += f"<th>{table_element.name}</th>"
        html_str += "</tr>"
        queryset = self.get_paginated_queryset()
        for query_object in queryset:
            html_str += '<tr style="white-space:nowrap;">'
            for table_element in self.table_elements:
                html_str += table_element.get_attribute(query_object, "html")
            html_str += "</tr>"
        html_str += "</table>"
        return html_str

    def to_latex(self):
        latex_str = "\\begin{table}\n\\centering\n\\\begin{tabularx}{\\textwidth}{|>{\\columncolor{white}}X|>{\\columncolor{lightblue}}X|}"

        for _ in self.table_elements:
            latex_str += "l|"
        latex_str += "}\n\\hline\n"
        for table_element in self.table_elements:
            if isinstance(table_element, te.LinkTableElement):
                continue
            latex_str += f"{table_element.name} & "
        latex_str = latex_str[:-2] + "\\\\\n\\hline\n"
        queryset = self.repository.std_queryset()
        for query_object in queryset:
            for table_element in self.table_elements:
                if isinstance(table_element, te.LinkTableElement):
                    continue
                latex_str += table_element.get_attribute(query_object, "latex")
            latex_str = latex_str[:-2] + "\\\\\n"
        latex_str += "\\hline\n\\end{tabularx}\n\\end{table}"
        return latex_str

    def get_paginated_queryset(self):
        queryset = self.repository.std_queryset()
        if self.is_paginated:
            return self._paginate_queryset(queryset)
        return queryset

    def _paginate_queryset(self, queryset):
        page_number = self.session_data.get("page", [1])[0]
        paginator = Paginator(queryset, self.paginate_by)
        page = paginator.get_page(page_number)
        return page

    def download_csv(self, response: HttpResponse) -> HttpResponse:
        queryset = self.repository.std_queryset()
        writer = csv.writer(response)
        csv_elements = [
            table_element
            for table_element in self.table_elements
            if not isinstance(table_element, te.LinkTableElement)
        ]
        writer.writerow([table_element.name for table_element in csv_elements])
        for row in queryset.all():
            values = []
            for element in csv_elements:
                if hasattr(element, "attr"):
                    values.append(getattr(row, element.attr))
                else:
                    values.append(getattr(row, element.text))

            writer.writerow(values)
        return response
