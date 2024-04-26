from baseclasses.managers.montrek_manager import MontrekManager
from reporting.dataclasses import table_elements as te
import csv
from django.views.generic.base import HttpResponse


class MontrekTableManager(MontrekManager):
    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return ()

    def to_html(self):
        html_str = '<table class="table table-bordered table-hover"><tr>'
        for table_element in self.table_elements:
            html_str += f"<th>{table_element.name}</th>"
        html_str += "</tr>"
        queryset = self.repository.std_queryset()
        for query_object in queryset:
            html_str += '<tr style="white-space:nowrap;">'
            for table_element in self.table_elements:
                html_str += table_element.get_attribute(query_object)
            html_str += "</tr>"
        html_str += "</table>"
        return html_str

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
