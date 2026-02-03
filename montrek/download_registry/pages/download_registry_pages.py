from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from download_registry.repositories.download_registry_repositories import (
    DownloadRegistryRepository,
)

PAGE_TITLE = "Download Registry"
LIST_TAB_NAME = "Download Registry"
DETAILS_TAB_NAME = "Download Registry"


class DownloadRegistryPage(MontrekPage):
    page_title = PAGE_TITLE

    def get_tabs(self):
        return (
            TabElement(
                name=LIST_TAB_NAME,
                link=reverse("download_registry_list"),
                html_id="tab_download_registry_list",
                active="active",
            ),
        )


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
