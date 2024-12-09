from montrek_example.repositories.sat_a1_repository import SatA1Repository
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.dataclasses import table_elements as te
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository


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


class HubAManager(MontrekTableManager):
    repository_class = HubARepository

    @property
    def table_elements(self) -> list:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
            te.StringTableElement(name="A2 String", attr="field_a2_str"),
            te.FloatTableElement(name="A2 Float", attr="field_a2_float"),
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
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


class SatA1Manager(MontrekTableManager):
    repository_class = SatA1Repository

    @property
    def table_elements(self) -> list:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
        )


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
                name="D2 String",
                text="field_d1_str",
                url="montrek_example_d_list",
                hover_text="View D Example",
                kwargs={"filter": "field_d1_str"},
            ),
            te.StringTableElement(name="D2 Int", attr="field_d1_int"),
            te.AlertTableElement(name="Alert Level", attr="alert_level"),
            te.StringTableElement(name="Alert Message", attr="alert_message"),
        ]


class HubCManager(MontrekTableManager):
    repository_class = HubCRepository

    @property
    def table_elements(self) -> list:
        return (
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            te.IntTableElement(name="B1 Date", attr="field_b1_date"),
            te.StringTableElement(name="B2 String", attr="field_b2_str"),
            te.StringTableElement(name="B2 Choice", attr="field_b2_choice"),
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
            te.LinkTableElement(
                name="Delete",
                url="montrek_example_d_delete",
                kwargs={"pk": "id"},
                icon="trash",
                hover_text="Delete Example D",
            ),
        ]
