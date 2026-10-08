from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository

PAGE_TITLE = "Sftp Connection"
LIST_TAB_NAME = "Sftp Connection"
DETAILS_TAB_NAME = "Sftp Connection"


class SftpConnectionPage(MontrekPage):
    page_title = PAGE_TITLE

    def get_tabs(self):
        return (
            TabElement(
                name=LIST_TAB_NAME,
                link=reverse("sftp_connection_list"),
                html_id="tab_sftp_connection_list",
                active="active",
            ),
            TabElement(
                name="Import Sources",
                link=reverse("sftp_import_source_list"),
                html_id="tab_sftp_import_source_list",
            ),
        )


class SftpConnectionDetailsPage(MontrekDetailsPage):
    repository_class = SftpConnectionRepository
    title_field = "hub_entity_id"

    def get_tabs(self):
        return (
            TabElement(
                name=DETAILS_TAB_NAME,
                link=reverse("sftp_connection_details", args=[self.obj.id]),
                html_id="tab_sftp_connection_details",
                active="active",
            ),
            TabElement(
                name="History",
                link=reverse("sftp_connection_history", args=[self.obj.id]),
                html_id="tab_sftp_connection_history",
            ),
        )
