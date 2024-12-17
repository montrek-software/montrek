from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement, UploadActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from file_upload.views import (
    FileUploadRegistryView,
    MontrekDownloadFileView,
    MontrekUploadFileView,
)
from showcase.managers.stransaction_managers import (
    STransactionFURegistryManager,
    STransactionTableManager,
    STransactionUploadManager,
)
from showcase.pages.stransaction_pages import STransactionPage
from showcase.forms.stransaction_forms import STransactionCreateForm
from showcase.views.sproduct_views import BackToProductListActionMixin


class STransactionCreateView(MontrekCreateView):
    manager_class = STransactionTableManager
    page_class = STransactionPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "Transaction Create"


class STransactionUpdateView(MontrekUpdateView):
    manager_class = STransactionTableManager
    page_class = STransactionPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "Transaction Update"


class STransactionDeleteView(MontrekDeleteView):
    manager_class = STransactionTableManager
    page_class = STransactionPage
    tab = "tab_stransaction_list"
    success_url = "stransaction_list"
    title = "Transaction Delete"


class STransactionListView(BackToProductListActionMixin, MontrekListView):
    manager_class = STransactionTableManager
    page_class = STransactionPage
    tab = "tab_stransaction_list"
    title = "All Transactions"

    @property
    def actions(self) -> tuple:
        actions = list(super().actions)
        action_new = ActionElement(
            icon="plus",
            link=reverse("stransaction_create"),
            action_id="id_create_transaction",
            hover_text="Create new Transaction",
        )
        actions.append(action_new)
        return tuple(actions)


class STransactionFURegistryView(BackToProductListActionMixin, FileUploadRegistryView):
    page_class = STransactionPage
    tab = "tab_stransaction_fu_registry_list"
    title = "Transaction File Upload Registry"
    manager_class = STransactionFURegistryManager

    @property
    def actions(self) -> tuple:
        actions = list(super().actions)
        action_upload_file = UploadActionElement(url_name="stransaction_upload_file")
        actions.append(action_upload_file)
        return tuple(actions)


class STransactionDownloadFileView(MontrekDownloadFileView):
    page_class = STransactionPage
    title = "Download Transaction File"
    manager_class = STransactionFURegistryManager


class STransactionUploadFileView(MontrekUploadFileView):
    page_class = STransactionPage
    tab = "tab_stransaction_fu_registry_list"
    title = "Upload Transaction File"
    file_upload_manager_class = STransactionUploadManager
    accept = ".csv"

    def get_success_url(self):
        return reverse("stransaction_fu_registry_list")
