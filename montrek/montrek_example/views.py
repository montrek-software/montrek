from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekHistoryListView
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekDeleteView
from baseclasses.views import MontrekUpdateView
from baseclasses.dataclasses.table_elements import (
    DateTableElement,
    LinkTextTableElement,
    StringTableElement,
)
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import IntTableElement
from baseclasses.dataclasses.table_elements import LinkTableElement

from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.forms import ExampleACreateForm
from montrek_example.forms import ExampleCCreateForm
from montrek_example.forms import ExampleBCreateForm
from montrek_example.pages import ExampleAPage, MontrekExampleAAppPage
from montrek_example.pages import MontrekExampleBAppPage
from montrek_example.pages import MontrekExampleCAppPage
from montrek_example.pages import MontrekExampleDAppPage


def action_back_to_overview(example: str):
    return ActionElement(
        icon="arrow-left",
        link=reverse(f"montrek_example_{example}_list"),
        action_id="back_to_overview",
        hover_text="Back to Overview",
    )


# Create your views here.


class MontrekExampleACreate(MontrekCreateView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
    form_class = ExampleACreateForm
    success_url = "montrek_example_a_list"


class MontrekExampleAUpdate(MontrekUpdateView):
    repository = HubARepository
    page_class = ExampleAPage
    form_class = ExampleACreateForm
    success_url = "montrek_example_a_list"


class MontrekExampleAList(MontrekListView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
    tab = "tab_example_a_list"
    title = "Example A List"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="A1 String", attr="field_a1_str"),
            IntTableElement(name="A1 Int", attr="field_a1_int"),
            StringTableElement(name="A2 String", attr="field_a2_str"),
            FloatTableElement(name="A2 Float", attr="field_a2_float"),
            StringTableElement(name="B1 String", attr="field_b1_str"),
            LinkTableElement(
                name="View",
                url="montrek_example_a_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Example A",
            ),
            LinkTableElement(
                name="Update",
                url="montrek_example_a_update",
                kwargs={"pk": "id"},
                icon="pencil",
                hover_text="View Example A",
            ),
            LinkTableElement(
                name="Delete",
                url="montrek_example_a_delete",
                kwargs={"pk": "id"},
                icon="trash",
                hover_text="Delete Example A",
            ),
        )

    @property
    def actions(self) -> tuple:
        action_new_example_a = ActionElement(
            icon="plus",
            link=reverse("montrek_example_a_create"),
            action_id="id_new_example_a",
            hover_text="Add new A Example",
        )
        return (action_new_example_a,)


class MontrekExampleADelete(MontrekDeleteView):
    repository = HubARepository
    page_class = ExampleAPage
    success_url = "montrek_example_a_list"


class MontrekExampleADetails(MontrekDetailView):
    repository = HubARepository
    page_class = ExampleAPage
    tab = "tab_details"
    title = "Example A Details"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="A1 String", attr="field_a1_str"),
            IntTableElement(name="A1 Int", attr="field_a1_int"),
            StringTableElement(name="A2 String", attr="field_a2_str"),
            FloatTableElement(name="A2 Float", attr="field_a2_float"),
            StringTableElement(name="B1 String", attr="field_b1_str"),
        )

    @property
    def actions(self) -> tuple:
        action_update_example_a = ActionElement(
            icon="pencil",
            link=reverse("montrek_example_a_update", kwargs=self.kwargs),
            action_id="id_update_example_a",
            hover_text="Update ExampleA",
        )
        return (action_back_to_overview("a"), action_update_example_a)


class MontrekExampleBCreate(MontrekCreateView):
    repository = HubBRepository
    page_class = MontrekExampleBAppPage
    success_url = "montrek_example_b_list"
    form_class = ExampleBCreateForm


class MontrekExampleBList(MontrekListView):
    repository = HubBRepository
    page_class = MontrekExampleBAppPage
    tab = "tab_example_b_list"

    @property
    def elements(self) -> list:
        return [
            StringTableElement(name="B1 String", attr="field_b1_str"),
            IntTableElement(name="B1 Date", attr="field_b1_date"),
            StringTableElement(name="B2 String", attr="field_b2_str"),
            StringTableElement(name="B2 Choice", attr="field_b2_choice"),
            LinkTextTableElement(
                name="D2 String",
                text="field_d1_str",
                url="montrek_example_d_list",
                hover_text="View D Example",
                kwargs={"filter": "field_d1_str"},
            ),
            StringTableElement(name="D2 Int", attr="field_d1_int"),
        ]

    @property
    def actions(self) -> tuple:
        action_new_example_b = ActionElement(
            icon="plus",
            link=reverse("montrek_example_b_create"),
            action_id="id_new_example_b",
            hover_text="Add new B Example",
        )
        return (action_back_to_overview("b"), action_new_example_b)

    success_url = "montrek_example_b_list"


class MontrekExampleAHistory(MontrekHistoryListView):
    repository = HubARepository
    page_class = ExampleAPage
    tab = "tab_history"
    title = "Example A History"

    @property
    def elements(self) -> tuple:
        return (
            StringTableElement(name="A1 String", attr="field_a1_str"),
            IntTableElement(name="A1 Int", attr="field_a1_int"),
            StringTableElement(name="A2 String", attr="field_a2_str"),
            FloatTableElement(name="A2 Float", attr="field_a2_float"),
            StringTableElement(name="B1 String", attr="field_b1_str"),
            DateTableElement(name="Change Date", attr="change_date"),
            StringTableElement(name="Changed By", attr="changed_by"),
            StringTableElement(name="Change Comment", attr="change_comment"),
        )

    @property
    def actions(self) -> tuple:
        return (action_back_to_overview("a"),)


class MontrekExampleCList(MontrekListView):
    repository = HubCRepository
    page_class = MontrekExampleCAppPage
    tab = "tab_example_c_list"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="B1 String", attr="field_b1_str"),
            IntTableElement(name="B1 Date", attr="field_b1_date"),
            StringTableElement(name="B2 String", attr="field_b2_str"),
            StringTableElement(name="B2 Choice", attr="field_b2_choice"),
        )

    @property
    def actions(self) -> tuple:
        action_new_example_c = ActionElement(
            icon="plus",
            link=reverse("montrek_example_c_create"),
            action_id="id_new_example_c",
            hover_text="Add new C Example",
        )
        return (action_back_to_overview("b"), action_new_example_c)

    success_url = "montrek_example_c_list"


class MontrekExampleCCreate(MontrekCreateView):
    repository = HubCRepository
    page_class = MontrekExampleCAppPage
    success_url = "montrek_example_c_list"
    form_class = ExampleCCreateForm


class MontrekExampleDList(MontrekListView):
    repository = HubDRepository
    page_class = MontrekExampleDAppPage
    tab = "tab_example_d_list"

    @property
    def elements(self) -> list:
        return [
            StringTableElement(name="D1 String", attr="field_d1_str"),
            IntTableElement(name="D1 Int", attr="field_d1_int"),
        ]

    @property
    def actions(self) -> tuple:
        action_new_example_d = ActionElement(
            icon="plus",
            link=reverse("montrek_example_d_create"),
            action_id="id_new_example_d",
            hover_text="Add new D Example",
        )
        return (action_back_to_overview("d"), action_new_example_d)

    success_url = "montrek_example_d_list"


class MontrekExampleDCreate(MontrekCreateView):
    repository = HubDRepository
    page_class = MontrekExampleDAppPage
    success_url = "montrek_example_d_list"
