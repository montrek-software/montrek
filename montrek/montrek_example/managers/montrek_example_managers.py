from reporting.managers.montrek_table_manager import MontrekTableManager
from baseclasses.dataclasses import table_elements as te
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository


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


class HubBManager(MontrekTableManager):
    repository_class = HubBRepository


class HubCManager(MontrekTableManager):
    repository_class = HubCRepository


class HubDManager(MontrekTableManager):
    repository_class = HubDRepository
