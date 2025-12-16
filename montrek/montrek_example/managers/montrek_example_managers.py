from baseclasses.typing import TableElementsType
from django.http import HttpResponse
from django.urls import reverse
from montrek_example.repositories.hub_a_repository import (
    HubARepository,
    HubARepository5,
)
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.repositories.sat_a1_repository import SatA1Repository
from reporting.core import reporting_text as rt
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import (
    HistoryDataTableManager,
    MontrekTableManager,
)


class ExampleReportManager(MontrekReportManager):
    report_name = "Example Report"

    def collect_report_elements(self) -> None:
        table_managers = [
            HubAManager(self.session_data),
            HubBManager(self.session_data),
            HubCManager(self.session_data),
        ]
        for table_manager in table_managers:
            self.append_report_element(table_manager)


class ExampleAReportManager(MontrekReportManager):
    report_name = "Example Report"
    repository_class = HubARepository

    def collect_report_elements(self) -> None:
        self.obj = self.get_object_from_pk(self.session_data["pk"])
        self.append_report_element(rt.ReportingHeader2("Test Header"))
        editable_element_a1 = rt.ReportingEditableText(
            self.obj,
            "field_a1_str",
            edit_url=reverse(
                "montrek_example_a_edit_field", kwargs={"pk": self.session_data["pk"]}
            ),
            header="Field A1 Str",
        )
        self.append_report_element(editable_element_a1)
        editable_element_a2 = rt.ReportingEditableText(
            self.obj,
            "field_a2_str",
            edit_url=reverse(
                "montrek_example_a_edit_field", kwargs={"pk": self.session_data["pk"]}
            ),
            header="Field A2 Str",
        )
        self.append_report_element(editable_element_a2)


class CompactHubAManager(MontrekTableManager):
    repository_class = HubARepository
    is_compact_format = True

    @property
    def table_elements(self) -> tuple:
        return (
            te.LinkTextTableElement(
                name="A1 String",
                url="montrek_example_a_details",
                kwargs={"pk": "hub_id"},
                text="field_a1_str",
                hover_text="View Example A",
            ),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
        )


class ExampleIndividualTableElement(te.FloatTableElement):
    def get_value(self, obj):
        return obj.field_a2_float * 2


class HubAManager(MontrekTableManager):
    repository_class = HubARepository

    @property
    def table_elements(self) -> tuple:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
            te.StringTableElement(name="A2 String", attr="field_a2_str"),
            te.FloatTableElement(name="A2 Float", attr="field_a2_float"),
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            ExampleIndividualTableElement(name="TestField", attr="individual_field"),
            te.LinkTableElement(
                name="View",
                url="montrek_example_a_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Example A",
            ),
            te.LinkTableElement(
                name="Update",
                url="montrek_example_a_update",
                kwargs={"pk": "id"},
                icon="pencil",
                hover_text="View Example A",
            ),
            te.LinkTableElement(
                name="Delete",
                url="montrek_example_a_delete",
                kwargs={"pk": "id"},
                icon="trash",
                hover_text="Delete Example A",
            ),
        )

    def download(self) -> HttpResponse:
        response = HttpResponse()
        df = self.get_df()
        df.to_markdown(response, index=False)
        return response

    def get_filename(self) -> str:
        return "example_md.txt"


class SatA1Manager(MontrekTableManager):
    repository_class = SatA1Repository

    @property
    def table_elements(self) -> list:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
        )


class SatA5Manager(MontrekTableManager):
    repository_class = HubARepository5

    @property
    def table_elements(self) -> TableElementsType:
        return (
            te.StringTableElement(name="A5 String", attr="field_a5_str"),
            te.SecretStringTableElement(name="Secret", attr="secret_field"),
        )


class SatA5HistoryManager(HistoryDataTableManager): ...


class HubADetailsManager(MontrekDetailsManager):
    repository_class = HubARepository

    @property
    def table_elements(self) -> list:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
            te.StringTableElement(name="A2 String", attr="field_a2_str"),
            te.FloatTableElement(name="A2 Float", attr="field_a2_float"),
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
        )


class HubBManager(MontrekTableManager):
    repository_class = HubBRepository

    @property
    def table_elements(self) -> list:
        return [
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            te.DateTableElement(name="B1 Date", attr="field_b1_date"),
            te.StringTableElement(name="B2 String", attr="field_b2_str"),
            te.StringTableElement(name="B2 Choice", attr="field_b2_choice"),
            te.LinkTextTableElement(
                name="D1 String",
                text="field_d1_str",
                url="montrek_example_d_list",
                hover_text="View D Example",
                kwargs={"filter": "field_d1_str"},
            ),
            te.LinkListTableElement(
                name="Linked D Objects",
                url="montrek_example_d_details",
                hover_text="View D Example",
                text="field_d1_str",
                list_attr="hub_d_id",
                list_kwarg="pk",
                in_separator=",",
            ),
            te.StringTableElement(name="D2 Int", attr="field_d1_int"),
            te.AlertTableElement(name="Alert Level", attr="alert_level"),
            te.StringTableElement(name="Alert Message", attr="alert_message"),
        ]


class ExampleBReportManager(MontrekReportManager):
    report_name = "Example Report"
    repository_class = HubBRepository

    def collect_report_elements(self) -> None:
        self.obj = self.get_object_from_pk(self.session_data["pk"])
        self.append_report_element(rt.ReportingHeader2("Test Header"))
        editable_element_a1 = rt.ReportingEditableText(
            self.obj,
            "field_b2_choice",
            edit_url=reverse(
                "montrek_example_b_edit_field", kwargs={"pk": self.session_data["pk"]}
            ),
            header="Field B2 Choice",
        )
        self.append_report_element(editable_element_a1)
        editable_element_a2 = rt.ReportingEditableText(
            self.obj,
            "alert_level",
            edit_url=reverse(
                "montrek_example_b_edit_field", kwargs={"pk": self.session_data["pk"]}
            ),
            header="Field Alert Level",
        )
        self.append_report_element(editable_element_a2)


class HubCManager(MontrekTableManager):
    repository_class = HubCRepository

    @property
    def table_elements(self) -> list:
        return (
            te.DateTableElement(name="Value Date", attr="value_date"),
            te.StringTableElement(name="C1 String", attr="field_c1_str"),
            te.IntTableElement(name="C1 Bool", attr="field_c1_bool"),
        )


class HubDManager(MontrekTableManager):
    repository_class = HubDRepository

    @property
    def table_elements(self) -> list:
        return [
            te.StringTableElement(name="D1 String", attr="field_d1_str"),
            te.IntTableElement(name="D1 Int", attr="field_d1_int"),
            te.DateTableElement(name="Value Date", attr="value_date"),
            te.FloatTableElement(name="D2 Float", attr="field_tsd2_float"),
            te.IntTableElement(name="D2 Int", attr="field_tsd2_int"),
            te.StringTableElement(name="Comment", attr="comment"),
            te.LinkTableElement(
                name="Delete",
                url="montrek_example_d_delete",
                kwargs={"pk": "id"},
                icon="trash",
                hover_text="Delete Example D",
            ),
        ]


class HubDDetailsManager(MontrekDetailsManager):
    repository_class = HubDRepository

    @property
    def table_elements(self) -> list:
        return [
            te.StringTableElement(name="D1 String", attr="field_d1_str"),
            te.IntTableElement(name="D1 Int", attr="field_d1_int"),
            te.DateTableElement(name="Value Date", attr="value_date"),
            te.FloatTableElement(name="D2 Float", attr="field_tsd2_float"),
            te.IntTableElement(name="D2 Int", attr="field_tsd2_int"),
            te.LinkTableElement(
                name="Delete",
                url="montrek_example_d_delete",
                kwargs={"pk": "id"},
                icon="trash",
                hover_text="Delete Example D",
            ),
        ]
