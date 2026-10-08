from django.urls import reverse

from baseclasses import views
from baseclasses.dataclasses.view_classes import ActionElement, ListActionElement
from sftp.forms.sftp_import_source_forms import SftpImportSourceCreateForm
from sftp.managers.sftp_import_scheduler_manager import SftpImportSchedulerManager
from sftp.managers.sftp_import_source_managers import (
    SftpImportedFileTableManager,
    SftpImportSourceDetailsManager,
    SftpImportSourceTableManager,
)
from sftp.pages.sftp_connection_pages import SftpConnectionPage
from sftp.pages.sftp_import_source_pages import SftpImportSourceDetailsPage

LIST_URL = "sftp_import_source_list"
LIST_TAB = "tab_sftp_import_source_list"


class SftpImportSourceCreateView(views.MontrekCreateView):
    manager_class = SftpImportSourceTableManager
    page_class = SftpConnectionPage
    tab = LIST_TAB
    form_class = SftpImportSourceCreateForm
    success_url = LIST_URL
    title = "Sftp Import Source Create"


class SftpImportSourceUpdateView(views.MontrekUpdateView):
    manager_class = SftpImportSourceTableManager
    page_class = SftpConnectionPage
    tab = LIST_TAB
    form_class = SftpImportSourceCreateForm
    success_url = LIST_URL
    title = "Sftp Import Source Update"


class SftpImportSourceDeleteView(views.MontrekDeleteView):
    manager_class = SftpImportSourceTableManager
    page_class = SftpConnectionPage
    tab = LIST_TAB
    success_url = LIST_URL
    title = "Sftp Import Source Delete"


class SftpImportSourceListView(views.MontrekListView):
    manager_class = SftpImportSourceTableManager
    page_class = SftpConnectionPage
    tab = LIST_TAB
    title = "Sftp Import Source List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sftp_import_source_create"),
            action_id="id_create_sftp_import_source",
            hover_text="Create new Sftp Import Source",
        )
        return (action_new,)


class SftpImportSourceDetailView(views.MontrekDetailView):
    manager_class = SftpImportSourceDetailsManager
    page_class = SftpImportSourceDetailsPage
    tab = "tab_sftp_import_source_details"
    title = "Sftp Import Source Details"

    @property
    def actions(self) -> tuple:
        return (ListActionElement(LIST_URL),)


class SftpImportSourceImportedFilesView(views.MontrekListView):
    manager_class = SftpImportedFileTableManager
    page_class = SftpImportSourceDetailsPage
    tab = "tab_sftp_import_source_imported_files"
    title = "Imported Files"

    @property
    def actions(self) -> tuple:
        return (ListActionElement(LIST_URL),)


class SftpImportSourceHistoryView(views.MontrekHistoryListView):
    manager_class = SftpImportSourceTableManager
    page_class = SftpImportSourceDetailsPage
    tab = "tab_sftp_import_source_history"
    title = "Sftp Import Source History"

    @property
    def actions(self) -> tuple:
        return (ListActionElement(LIST_URL),)


class SftpImportSourceSyncView(views.MontrekPostActionView):
    """Queue a poll of the source; pk is its hub id."""

    manager_class = SftpImportSchedulerManager

    def run_action(self) -> None:
        self.manager.schedule_sync()

    def get_redirect_url(self, *args, **kwargs) -> str:
        return reverse(LIST_URL)
