from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.asset_sat_factories import SAssetTypeFactory
from showcase.views.asset_views import SAssetCreateView
from showcase.views.asset_views import SAssetUpdateView
from showcase.views.asset_views import SAssetListView
from showcase.views.asset_views import SAssetDeleteView


class TestSAssetCreateView(MontrekCreateViewTestCase):
    viewname = "asset_create"
    view_class = SAssetCreateView

    def creation_data(self):
        return {}


class TestSAssetUpdateView(MontrekUpdateViewTestCase):
    viewname = "asset_update"
    view_class = SAssetUpdateView

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSAssetListView(MontrekListViewTestCase):
    viewname = "asset_list"
    view_class = SAssetListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()


class TestSAssetDeleteView(MontrekDeleteViewTestCase):
    viewname = "asset_delete"
    view_class = SAssetDeleteView

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
