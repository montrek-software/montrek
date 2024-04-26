from baseclasses.managers.montrek_manager import MontrekManager
from reporting.dataclasses.table_elements import TableElement


class MontrekTableManager(MontrekManager):
    @property
    def table_elements(self) -> tuple[TableElement, ...]:
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
