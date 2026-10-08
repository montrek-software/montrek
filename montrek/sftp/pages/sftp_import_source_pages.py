from django.urls import reverse

from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportSourceRepository,
)


class SftpImportSourceDetailsPage(MontrekDetailsPage):
    repository_class = SftpImportSourceRepository
    title_field = "name"

    def get_tabs(self):
        return (
            TabElement(
                name="Sftp Import Source",
                link=reverse("sftp_import_source_details", args=[self.obj.hub_id]),
                html_id="tab_sftp_import_source_details",
                active="active",
            ),
            TabElement(
                name="Imported Files",
                link=reverse(
                    "sftp_import_source_imported_files", args=[self.obj.hub_id]
                ),
                html_id="tab_sftp_import_source_imported_files",
            ),
            TabElement(
                name="History",
                link=reverse("sftp_import_source_history", args=[self.obj.id]),
                html_id="tab_sftp_import_source_history",
            ),
        )
