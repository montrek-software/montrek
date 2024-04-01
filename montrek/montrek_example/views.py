from baseclasses import views
from baseclasses.dataclasses import table_elements as te
from baseclasses.dataclasses.view_classes import ActionElement
from django.urls import reverse
from file_upload.views import (
    MontrekFieldMapCreateView,
    MontrekFieldMapListView,
    MontrekUploadFileView,
    MontrekUploadView,
)
from montrek_example.repositories.sat_a1_repository import SatA1Repository
from montrek_example.managers.a1_file_upload_manager import (
    A1FieldMapManager,
    AFileUploadProcessor,
)

from montrek_example import forms, pages
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository


def action_back_to_overview(example: str):
    return ActionElement(
        icon="arrow-left",
        link=reverse(f"montrek_example_{example}_list"),
        action_id="back_to_overview",
        hover_text="Back to Overview",
    )


# Create your views here.


class MontrekExampleACreate(views.MontrekCreateView):
    repository = HubARepository
    page_class = pages.MontrekExampleAAppPage
    form_class = forms.ExampleACreateForm
    success_url = "montrek_example_a_list"


class MontrekExampleAUpdate(views.MontrekUpdateView):
    repository = HubARepository
    page_class = pages.ExampleAPage
    form_class = forms.ExampleACreateForm
    success_url = "montrek_example_a_list"


class MontrekExampleAList(views.MontrekListView):
    repository = HubARepository
    page_class = pages.MontrekExampleAAppPage
    tab = "tab_example_a_list"
    title = "Example A List"

    @property
    def elements(self) -> list:
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

    @property
    def actions(self) -> tuple:
        action_new_example_a = ActionElement(
            icon="plus",
            link=reverse("montrek_example_a_create"),
            action_id="id_new_example_a",
            hover_text="Add new A Example",
        )
        return (action_new_example_a,)


class MontrekExampleADelete(views.MontrekDeleteView):
    repository = HubARepository
    page_class = pages.ExampleAPage
    success_url = "montrek_example_a_list"


class MontrekExampleADetails(views.MontrekDetailView):
    repository = HubARepository
    page_class = pages.ExampleAPage
    tab = "tab_details"
    title = "Example A Details"

    @property
    def elements(self) -> list:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
            te.StringTableElement(name="A2 String", attr="field_a2_str"),
            te.FloatTableElement(name="A2 Float", attr="field_a2_float"),
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
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


class MontrekExampleBCreate(views.MontrekCreateView):
    repository = HubBRepository
    page_class = pages.MontrekExampleBAppPage
    success_url = "montrek_example_b_list"
    form_class = forms.ExampleBCreateForm


class MontrekExampleBList(views.MontrekListView):
    repository = HubBRepository
    page_class = pages.MontrekExampleBAppPage
    tab = "tab_example_b_list"

    @property
    def elements(self) -> list:
        return [
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            te.IntTableElement(name="B1 Date", attr="field_b1_date"),
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


class MontrekExampleAHistory(views.MontrekHistoryListView):
    repository = HubARepository
    page_class = pages.ExampleAPage
    tab = "tab_history"
    title = "Example A History"

    @property
    def elements(self) -> tuple:
        return (
            te.StringTableElement(name="A1 String", attr="field_a1_str"),
            te.IntTableElement(name="A1 Int", attr="field_a1_int"),
            te.StringTableElement(name="A2 String", attr="field_a2_str"),
            te.FloatTableElement(name="A2 Float", attr="field_a2_float"),
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            te.DateTableElement(name="Change Date", attr="change_date"),
            te.StringTableElement(name="Changed By", attr="changed_by"),
            te.StringTableElement(name="Change Comment", attr="change_comment"),
        )

    @property
    def actions(self) -> tuple:
        return (action_back_to_overview("a"),)


class MontrekExampleCList(views.MontrekListView):
    repository = HubCRepository
    page_class = pages.MontrekExampleCAppPage
    tab = "tab_example_c_list"

    @property
    def elements(self) -> list:
        return (
            te.StringTableElement(name="B1 String", attr="field_b1_str"),
            te.IntTableElement(name="B1 Date", attr="field_b1_date"),
            te.StringTableElement(name="B2 String", attr="field_b2_str"),
            te.StringTableElement(name="B2 Choice", attr="field_b2_choice"),
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


class MontrekExampleCCreate(views.MontrekCreateView):
    repository = HubCRepository
    page_class = pages.MontrekExampleCAppPage
    success_url = "montrek_example_c_list"
    form_class = forms.ExampleCCreateForm


class MontrekExampleDList(views.MontrekListView):
    repository = HubDRepository
    page_class = pages.MontrekExampleDAppPage
    tab = "tab_example_d_list"

    @property
    def elements(self) -> list:
        return [
            te.StringTableElement(name="D1 String", attr="field_d1_str"),
            te.IntTableElement(name="D1 Int", attr="field_d1_int"),
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


class MontrekExampleDCreate(views.MontrekCreateView):
    repository = HubDRepository
    page_class = pages.MontrekExampleDAppPage
    success_url = "montrek_example_d_list"


class MontrekExampleA1UploadFileView(MontrekUploadFileView):
    page_class = pages.MontrekExampleAAppPage
    title = "Upload A1 File"
    repository = HubARepository
    file_upload_processor_class = AFileUploadProcessor
    accept = ".csv"

    def get_success_url(self):
        return reverse("a1_view_uploads")


class MontrekExampleA1UploadView(MontrekUploadView):
    title = 'A1 Uploads'
    page_class = pages.MontrekExampleAAppPage
    repository = SatA1Repository

    def get_view_queryset(self):
        return self.repository().get_upload_registry_table()

    @property
    def actions(self) -> tuple:
        action_upload_file = ActionElement(
            icon="upload",
            link=reverse("a1_upload_file"),
            action_id="id_a_upload",
            hover_text="Upload A1 data from file",
        )
        return (action_upload_file,)


class MontrekExampleA1FieldMapCreateView(MontrekFieldMapCreateView):
    success_url = "montrek_example_a1_field_map_list"
    page_class = pages.MontrekExampleAAppPage
    field_map_manager_class = A1FieldMapManager
    related_repository_class = SatA1Repository

class MontrekExampleA1FieldMapListView(MontrekFieldMapListView):
    page_class = pages.MontrekExampleAAppPage
    tab = "tab_a1_field_map_list"

    @property
    def actions(self) -> tuple:
        action_new_field_map = ActionElement(
            icon="plus",
            link=reverse("montrek_example_a1_field_map_create"),
            action_id="id_new_a1_field_map",
            hover_text="Add new A1 Field Map",
        )
        return (action_new_field_map,)

    success_url = "montrek_example_a1_field_map_list"
