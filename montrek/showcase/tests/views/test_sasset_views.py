from showcase.factories.sasset_hub_factories import SAssetHubValueDateFactory
from showcase.models.sasset_sat_models import SAssetTypes
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekViewTestCase,
)
from showcase.factories.sasset_sat_factories import SAssetStaticSatelliteFactory
from showcase.views.sasset_views import SAssetCreateView, SAssetDetailView
from showcase.views.sasset_views import SAssetUpdateView
from showcase.views.sasset_views import SAssetListView
from showcase.views.sasset_views import SAssetDeleteView


class TestSAssetCreateView(MontrekCreateViewTestCase):
    viewname = "sasset_create"
    view_class = SAssetCreateView

    def creation_data(self):
        return {"asset_name": "Test Asset", "asset_type": SAssetTypes.BOND.value}


class TestSAssetUpdateView(MontrekUpdateViewTestCase):
    viewname = "sasset_update"
    view_class = SAssetUpdateView

    def build_factories(self):
        self.sat_obj = SAssetStaticSatelliteFactory(
            asset_name="Test Asset", asset_type=SAssetTypes.BOND.value
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {"asset_name": "Test Asset", "asset_type": SAssetTypes.EQUITY.value}


class TestSAssetListView(MontrekListViewTestCase):
    viewname = "sasset_list"
    view_class = SAssetListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SAssetStaticSatelliteFactory()


class TestSAssetDeleteView(MontrekDeleteViewTestCase):
    viewname = "sasset_delete"
    view_class = SAssetDeleteView

    def build_factories(self):
        self.sat_obj = SAssetStaticSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestSAssetDetailView(MontrekViewTestCase):
    viewname = "sasset_details"
    view_class = SAssetDetailView

    def build_factories(self):
        self.hub_vd = SAssetHubValueDateFactory(value_date=None)
        SAssetStaticSatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}
