from django.contrib import messages
from django.http import HttpResponseRedirect
from baseclasses import views
from montrek_example.managers.a_upload_table_manager import (
    HubAUploadTableManager,
)
from baseclasses.dataclasses.view_classes import ActionElement
from django.urls import reverse
from file_upload.views import (
    MontrekFieldMapCreateView,
    MontrekFieldMapListView,
    MontrekUploadFileView,
    MontrekUploadView,
)
from montrek_example.managers.a2_api_upload_manager import A2ApiUploadManager
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


class MontrekExampleReport(views.MontrekReportView):
    page_class = pages.MontrekExampleAAppPage
    manager_class = mem.ExampleReportManager
    title = "Montrek Example Report"


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
    manager_class = mem.HubADetailsManager
    page_class = pages.ExampleAPage
    tab = "tab_details"
    title = "Example A Details"

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
    def actions(self) -> tuple:
        return (action_back_to_overview("a"),)


class MontrekExampleCList(views.MontrekListView):
    manager_class = mem.HubCManager
    page_class = pages.MontrekExampleCAppPage
    tab = "tab_example_c_list"
    title = "Example C List"

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


class MontrekExampleHubAApiUploadView(views.MontrekListView):
    manager_class = HubAUploadTableManager
    page_class = pages.MontrekExampleAAppPage
    tab = "tab_hub_a_uploads"
    title = "A API Uploads"

    @property
    def actions(self) -> tuple:
        action_do_a2_upload = ActionElement(
            icon="upload",
            link=reverse("do_a2_upload"),
            action_id="id_do_a2_upload",
            hover_text="Upload A2 data from API",
        )
        return (action_do_a2_upload,)


def do_a2_upload(request):
    manager = A2ApiUploadManager(
        session_data={"user_id": request.user.id},
    )
    manager.upload_and_process()
    for m in manager.messages:
        getattr(messages, m.message_type)(request, m.message)
    return HttpResponseRedirect(reverse("hub_a_view_api_uploads"))
