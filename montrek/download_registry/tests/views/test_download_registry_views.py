from testing.test_cases.view_test_cases import (
    MontrekViewTestCase,
    MontrekListViewTestCase,
)
from download_registry.tests.factories.download_registry_hub_factories import (
    DownloadRegistryHubValueDateFactory,
)
from download_registry.tests.factories.download_registry_sat_factories import (
    DownloadRegistrySatelliteFactory,
)
from download_registry.views.download_registry_views import DownloadRegistryListView
from download_registry.views.download_registry_views import DownloadRegistryDetailView
from download_registry.views.download_registry_views import DownloadRegistryHistoryView


class TestDownloadRegistryListView(MontrekListViewTestCase):
    viewname = "download_registry_list"
    view_class = DownloadRegistryListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = DownloadRegistrySatelliteFactory()


class TestDownloadRegistryDetailView(MontrekViewTestCase):
    viewname = "download_registry_details"
    view_class = DownloadRegistryDetailView

    def build_factories(self):
        self.hub_vd = DownloadRegistryHubValueDateFactory(value_date=None)
        DownloadRegistrySatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}


class TestDownloadRegistryHistoryView(MontrekViewTestCase):
    viewname = "download_registry_history"
    view_class = DownloadRegistryHistoryView

    def build_factories(self):
        self.hub_vd = DownloadRegistryHubValueDateFactory(value_date=None)
        DownloadRegistrySatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.id}
