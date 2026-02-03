from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from django.urls import reverse

from info.repositories.download_registry_repositories import DownloadRegistryRepository

PAGE_TITLE = "Download Registry"
LIST_TAB_NAME = "Download Registry"
DETAILS_TAB_NAME = "Download Registry"


class InfoPage(MontrekPage):
    page_title = "Montrek Infos"

    def get_tabs(self) -> tuple[TabElement]:
        db_structure_tab = TabElement(
            name="DB Structure",
            link=reverse("db_structure"),
            html_id="id_db_structure",
        )
        info_tab = TabElement(
            name="Versions",
            link=reverse("info"),
            html_id="id_info",
        )
        admin_tab = TabElement(
            name="Admin",
            link=reverse("admin"),
            html_id="id_admin",
        )
        download_registry_tab = (
            TabElement(
                name=LIST_TAB_NAME,
                link=reverse("download_registry_list"),
                html_id="tab_download_registry_list",
                active="active",
            ),
        )
        return (db_structure_tab, info_tab, admin_tab, download_registry_tab)


class DownloadRegistryDetailsPage(MontrekDetailsPage):
    repository_class = DownloadRegistryRepository
    title_field = "hub_entity_id"

    def get_tabs(self):
        return (
            TabElement(
                name=DETAILS_TAB_NAME,
                link=reverse("download_registry_details", args=[self.obj.id]),
                html_id="tab_download_registry_details",
                active="active",
            ),
            TabElement(
                name="History",
                link=reverse("download_registry_history", args=[self.obj.id]),
                html_id="tab_download_registry_history",
            ),
        )
