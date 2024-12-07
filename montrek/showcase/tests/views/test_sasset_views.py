from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.sasset_sat_factories import SAssetTypeFactory
from showcase.views.sasset_views import SAssetCreateView
from showcase.views.sasset_views import SAssetUpdateView
from showcase.views.sasset_views import SAssetListView
from showcase.views.sasset_views import SAssetDeleteView


class TestSAssetCreateView(MontrekCreateViewTestCase):
    viewname = "sasset_create"
    view_class = SAssetCreateView

    def creation_data(self):
        return {}


class TestSAssetUpdateView(MontrekUpdateViewTestCase):
    viewname = "sasset_update"
    view_class = SAssetUpdateView

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSAssetListView(MontrekListViewTestCase):
    viewname = "sasset_list"
    view_class = SAssetListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()


class TestSAssetDeleteView(MontrekDeleteViewTestCase):
    viewname = "sasset_delete"
    view_class = SAssetDeleteView

    def build_factories(self):
        self.sat_obj = SAssetTypeFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
