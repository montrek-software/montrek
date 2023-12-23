from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekEditView
from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import IntTableElement
from baseclasses.dataclasses.table_elements import LinkTableElement

from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.forms import ExampleACreateForm
from montrek_example.pages import MontrekExampleAAppPage
from montrek_example.pages import MontrekExampleBAppPage


# Create your views here.


class MontrekExampleACreate(MontrekCreateView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
    form_class = ExampleACreateForm
    success_url = "montrek_example_a_list"

class MontrekExampleAEdit(MontrekEditView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
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
                name="Edit",
                url="montrek_example_a_edit",
                kwargs={"pk": "id"},
                icon="pencil",
                hover_text="View Example A",
            ),
        )

class MontrekExampleADetails(MontrekDetailView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="A1 String", attr="field_a1_str"),
            IntTableElement(name="A1 Int", attr="field_a1_int"),
            StringTableElement(name="A2 String", attr="field_a2_str"),
            FloatTableElement(name="A2 Float", attr="field_a2_float"),
            StringTableElement(name="B1 String", attr="field_b1_str"),
        )

class MontrekExampleBCreate(MontrekCreateView):
    repository = HubBRepository
    page_class = MontrekExampleBAppPage
    success_url = "montrek_example_b_list"


class MontrekExampleBList(MontrekListView):
    repository = HubBRepository
    page_class = MontrekExampleBAppPage
    tab = "tab_example_b_list"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="B1 String", attr="field_b1_str"),
            IntTableElement(name="B1 Date", attr="field_b1_date"),
            StringTableElement(name="B2 String", attr="field_b2_str"),
            StringTableElement(name="B2 Choice", attr="field_b2_choice"),
        )
