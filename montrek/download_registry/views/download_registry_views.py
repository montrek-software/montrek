from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement, ListActionElement
from baseclasses import views
from download_registry.managers.download_registry_managers import (
    DownloadRegistryTableManager,
)
from download_registry.managers.download_registry_managers import (
    DownloadRegistryDetailsManager,
)
from download_registry.pages.download_registry_pages import DownloadRegistryPage
from download_registry.pages.download_registry_pages import DownloadRegistryDetailsPage


class DownloadRegistryListView(views.MontrekListView):
    manager_class = DownloadRegistryTableManager
    page_class = DownloadRegistryPage
    tab = "tab_download_registry_list"
    title = "Download Registry List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("download_registry_create"),
            action_id="id_create_download_registry",
            hover_text="Create new Download Registry",
        )
        return (action_new,)


class DownloadRegistryDetailView(views.MontrekDetailView):
    manager_class = DownloadRegistryDetailsManager
    page_class = DownloadRegistryDetailsPage
    tab = "tab_download_registry_details"
    title = "Download Registry Details"

    @property
    def actions(self) -> tuple:
        action_back = ListActionElement("download_registry_list")
        return (action_back,)


class DownloadRegistryHistoryView(views.MontrekHistoryListView):
    manager_class = DownloadRegistryTableManager
    page_class = DownloadRegistryDetailsPage
    tab = "tab_download_registry_history"
    title = "Download Registry History"

    @property
    def actions(self) -> tuple:
        action_back = ListActionElement("download_registry_list")
        return (action_back,)
