import time
from django.contrib import messages
from django.http import HttpResponseRedirect
from baseclasses import views
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
    SEQUENTIAL_QUEUE_NAME,
    app as celery_app,
)
from requesting.views.authenticator_views import (
    AuthenticatorUserPasswordView,
)
from montrek_example.managers.a_upload_table_manager import (
    HubAFileUploadRegistryManager,
    HubAUploadTableManager,
)
from baseclasses.dataclasses.view_classes import (
    ActionElement,
    CreateActionElement,
    UploadActionElement,
)
from django.urls import reverse
from file_upload.views import (
    FileUploadRegistryView,
    MontrekFieldMapCreateView,
    MontrekFieldMapUpdateView,
    MontrekFieldMapListView,
    MontrekUploadFileView,
    MontrekDownloadFileView,
    MontrekDownloadLogFileView,
)
from montrek_example.managers.a2_api_upload_manager import A2ApiUploadManager
from montrek_example.managers.a1_file_upload_manager import (
    A1FileUploadManager,
)
from montrek_example.managers.a1_field_map_manager import (
    A1FieldMapManager,
)

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
        action_run_sequential_task = ActionElement(
            icon="option-horizontal",
            link=reverse("run_example_sequential_task"),
            action_id="id_run_sequential_task",
            hover_text="Run sequential task",
        )
        action_run_parallel_task = ActionElement(
            icon="option-vertical",
            link=reverse("run_example_parallel_task"),
            action_id="id_run_parallel_task",
            hover_text="Run parallel task",
        )
        return (
            action_new_example_a,
            action_run_sequential_task,
            action_run_parallel_task,
        )


class MontrekExampleADownloadView(views.MontrekDownloadView):
    manager_class = mem.HubAManager
    page_class = pages.ExampleAPage


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


class MontrekExampleBUpdate(views.MontrekUpdateView):
    manager_class = mem.HubBManager
    page_class = pages.MontrekExampleBAppPage
    success_url = "montrek_example_b_list"
    form_class = forms.ExampleBCreateForm
    title = "Update Example B"


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
        action_new_example_c = CreateActionElement(
            url_name="montrek_example_c_create",
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
    do_simple_file_upload = True

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


class MontrekExampleDDelete(views.MontrekDeleteView):
    manager_class = mem.HubDManager
    page_class = pages.MontrekExampleDAppPage
    success_url = "montrek_example_d_list"
    title = "Delete Example D"


class MontrekExampleA1UploadFileView(MontrekUploadFileView):
    page_class = pages.MontrekExampleAAppPage
    title = "Upload A1 File"
    file_upload_manager_class = A1FileUploadManager
    accept = ".csv"

    def get_success_url(self):
        return reverse("a1_view_uploads")


class MontrekExampleA1UploadView(FileUploadRegistryView):
    title = "A1 Uploads"
    page_class = pages.MontrekExampleAAppPage
    manager_class = HubAFileUploadRegistryManager

    @property
    def actions(self) -> tuple:
        action_upload_file = UploadActionElement(
            url_name="a1_upload_file",
            hover_text="Upload A1 data from file",
        )
        return (action_upload_file,)


class MontrekExampleA1FieldMapCreateView(MontrekFieldMapCreateView):
    success_url = "montrek_example_a1_field_map_list"
    page_class = pages.MontrekExampleAAppPage
    manager_class = A1FieldMapManager
    title = "Create A1 Field Map"


class MontrekExampleA1FieldMapUpdateView(MontrekFieldMapUpdateView):
    success_url = "montrek_example_a1_field_map_list"
    page_class = pages.MontrekExampleAAppPage
    manager_class = A1FieldMapManager
    title = "Update A1 Field Map"


class MontrekExampleA1FieldMapDeleteView(views.MontrekDeleteView):
    success_url = "montrek_example_a1_field_map_list"
    page_class = pages.MontrekExampleAAppPage
    manager_class = A1FieldMapManager
    title = "Delete A1 Field Map"


class MontrekExampleA1FieldMapListView(MontrekFieldMapListView):
    manager_class = A1FieldMapManager
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
        action_do_a2_upload = UploadActionElement(
            url_name="do_a2_upload",
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


class A2ApiUploadView(AuthenticatorUserPasswordView):
    page_class = pages.MontrekExampleAAppPage


class MontrekExampleA1DownloadFileView(MontrekDownloadFileView):
    manager_class = HubAFileUploadRegistryManager
    page_class = pages.MontrekExampleAAppPage
    title = "Download A1 File"


class MontrekExampleA1DownloadLogFileView(MontrekDownloadLogFileView):
    manager_class = HubAFileUploadRegistryManager
    page_class = pages.MontrekExampleAAppPage
    title = "Download A1 File"


class MontrekExampleA1UploadHistoryView(views.MontrekHistoryListView):
    manager_class = HubAFileUploadRegistryManager
    page_class = pages.MontrekExampleAAppPage
    title = "A1 Upload History"

    @property
    def actions(self) -> tuple:
        return (action_back_to_overview("a"),)

    success_url = "montrek_example_a1_upload_history"


@celery_app.task(queue=PARALLEL_QUEUE_NAME)
def example_parallel_task():
    time.sleep(10)
    return "Hello from parallel task!"


def do_run_example_parallel_task(request):
    example_parallel_task.delay()
    messages.info(request, "Parallel task started")
    return HttpResponseRedirect(reverse("montrek_example_a_list"))


@celery_app.task(queue=SEQUENTIAL_QUEUE_NAME)
def example_sequential_task():
    time.sleep(10)
    return "Hello from sequential task!"


def do_run_example_sequential_task(request):
    example_sequential_task.delay()
    messages.info(request, "Sequential task started")
    return HttpResponseRedirect(reverse("montrek_example_a_list"))


class HubARestApiView(views.MontrekRestApiView):
    manager_class = mem.HubAManager


class HubBRestApiView(views.MontrekRestApiView):
    manager_class = mem.HubBManager


class HubARedirectView(views.MontrekRedirectView):
    manager_class = mem.HubAManager
    page_class = pages.ExampleAPage
    title = "Redirect to Example A"

    def get_redirect_url(self, *args, **kwargs):
        return reverse("montrek_example_a_list")
