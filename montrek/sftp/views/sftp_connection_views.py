from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement, ListActionElement
from baseclasses import views
from sftp.managers.sftp_connection_managers import SftpConnectionTableManager
from sftp.managers.sftp_connection_managers import SftpConnectionDetailsManager
from sftp.pages.sftp_connection_pages import SftpConnectionPage
from sftp.pages.sftp_connection_pages import SftpConnectionDetailsPage
from sftp.forms.sftp_connection_forms import SftpConnectionCreateForm


class SftpConnectionCreateView(views.MontrekCreateView):
    manager_class = SftpConnectionTableManager
    page_class = SftpConnectionPage
    tab = "tab_sftp_connection_list"
    form_class = SftpConnectionCreateForm
    success_url = "sftp_connection_list"
    title = "Sftp Connection Create"


class SftpConnectionUpdateView(views.MontrekUpdateView):
    manager_class = SftpConnectionTableManager
    page_class = SftpConnectionPage
    tab = "tab_sftp_connection_list"
    form_class = SftpConnectionCreateForm
    success_url = "sftp_connection_list"
    title = "Sftp Connection Update"


class SftpConnectionDeleteView(views.MontrekDeleteView):
    manager_class = SftpConnectionTableManager
    page_class = SftpConnectionPage
    tab = "tab_sftp_connection_list"
    success_url = "sftp_connection_list"
    title = "Sftp Connection Delete"


class SftpConnectionListView(views.MontrekListView):
    manager_class = SftpConnectionTableManager
    page_class = SftpConnectionPage
    tab = "tab_sftp_connection_list"
    title = "Sftp Connection List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sftp_connection_create"),
            action_id="id_create_sftp_connection",
            hover_text="Create new Sftp Connection",
        )
        return (action_new,)


class SftpConnectionDetailView(views.MontrekDetailView):
    manager_class = SftpConnectionDetailsManager
    page_class = SftpConnectionDetailsPage
    tab = "tab_sftp_connection_details"
    title = "Sftp Connection Details"

    @property
    def actions(self) -> tuple:
        action_back = ListActionElement("sftp_connection_list")
        return (action_back,)


class SftpConnectionHistoryView(views.MontrekHistoryListView):
    manager_class = SftpConnectionTableManager
    page_class = SftpConnectionDetailsPage
    tab = "tab_sftp_connection_history"
    title = "Sftp Connection History"

    @property
    def actions(self) -> tuple:
        action_back = ListActionElement("sftp_connection_list")
        return (action_back,)
