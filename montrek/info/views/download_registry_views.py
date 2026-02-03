from baseclasses.dataclasses.view_classes import ListActionElement
from baseclasses import views
from info.managers.download_registry_managers import (
    DownloadRegistryTableManager,
)
from info.managers.download_registry_managers import (
    DownloadRegistryDetailsManager,
)
from info.pages import DownloadRegistryDetailsPage, InfoPage


class DownloadRegistryListView(views.MontrekListView):
    manager_class = DownloadRegistryTableManager
    page_class = InfoPage
    tab = "tab_download_registry_list"
    title = "Download Registry List"


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
