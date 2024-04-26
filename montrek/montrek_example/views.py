from baseclasses import views
from reporting.dataclasses import table_elements as te
from baseclasses.dataclasses.view_classes import ActionElement
from django.urls import reverse
from file_upload.views import (
    MontrekFieldMapCreateView,
    MontrekFieldMapListView,
    MontrekUploadFileView,
    MontrekUploadView,
)
from montrek_example.managers.a1_file_upload_manager import (
    A1FileUploadProcessor,
)
from montrek_example.managers.a1_field_map_manager import (
    A1FieldMapManager,
)
from montrek_example.repositories.sat_a1_repository import SatA1Repository

from montrek_example import forms, pages
from montrek_example.managers import montrek_example_managers as mem


def action_back_to_overview(example: str):
    return ActionElement(
        icon="arrow-left",
        link=reverse(f"montrek_example_{example}_list"),
        action_id="back_to_overview",
        hover_text="Back to Overview",
    )


# Create your views here.


class MontrekExampleACreate(views.MontrekCreateView):
    manager_class = mem.HubAManager
    page_class = pages.MontrekExampleAAppPage
    form_class = forms.ExampleACreateForm
    success_url = "montrek_example_a_list"
    title = "Create Example A"


class MontrekExampleAUpdate(views.MontrekUpdateView):
    manager_class = mem.HubAManager
    page_class = pages.ExampleAPage
    form_class = forms.ExampleACreateForm
    success_url = "montrek_example_a_list"
    title = "Update Example A"


class MontrekExampleAList(views.MontrekListView):
    manager_class = mem.HubAManager
    page_class = pages.MontrekExampleAAppPage
    tab = "tab_example_a_list"
    title = "Example A List"

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
    manager_class = mem.HubAManager
    page_class = pages.ExampleAPage
    success_url = "montrek_example_a_list"
    title = "Delete Example A"


class MontrekExampleADetails(views.MontrekDetailView):
    manager_class = mem.HubAManager
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
    manager_class = mem.HubBManager
    page_class = pages.MontrekExampleBAppPage
    success_url = "montrek_example_b_list"
    form_class = forms.ExampleBCreateForm
    title = "Create Example B"


class MontrekExampleBList(views.MontrekListView):
    manager_class = mem.HubBManager
    page_class = pages.MontrekExampleBAppPage
    tab = "tab_example_b_list"
    title = "Example B List"

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
            te.AlertTableElement(name="Alert Level", attr="alert_level"),
            te.StringTableElement(name="Alert Message", attr="alert_message"),
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
    manager_class = mem.HubAManager
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
    manager_class = mem.HubCManager
    page_class = pages.MontrekExampleCAppPage
    tab = "tab_example_c_list"
    title = "Example C List"

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
    manager_class = mem.HubCManager
    page_class = pages.MontrekExampleCAppPage
    success_url = "montrek_example_c_list"
    form_class = forms.ExampleCCreateForm
    title = "Create Example C"


class MontrekExampleDList(views.MontrekListView):
    manager_class = mem.HubDManager
    page_class = pages.MontrekExampleDAppPage
    tab = "tab_example_d_list"
    title = "Example D List"

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
    manager_class = mem.HubDManager
    page_class = pages.MontrekExampleDAppPage
    success_url = "montrek_example_d_list"
    permission_required = ["montrek_example.add_hubd"]
    title = "Create Example D"


class MontrekExampleA1UploadFileView(MontrekUploadFileView):
    manager_class = mem.HubAManager
    page_class = pages.MontrekExampleAAppPage
    title = "Upload A1 File"
    file_upload_processor_class = A1FileUploadProcessor
    accept = ".csv"

    def get_success_url(self):
        return reverse("a1_view_uploads")


class MontrekExampleA1UploadView(MontrekUploadView):
    manager_class = mem.HubAManager
    title = "A1 Uploads"
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
    title = "Create A1 Field Map"


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
