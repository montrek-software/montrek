from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.product_sat_factories import ProductSatelliteFactory
from showcase.views.product_views import ProductCreateView
from showcase.views.product_views import ProductUpdateView
from showcase.views.product_views import ProductListView
from showcase.views.product_views import ProductDeleteView


class TestProductCreateView(MontrekCreateViewTestCase):
    viewname = "product_create"
    view_class = ProductCreateView

    def creation_data(self):
        return {}


class TestProductUpdateView(MontrekUpdateViewTestCase):
    viewname = "product_update"
    view_class = ProductUpdateView

    def build_factories(self):
        self.sat_obj = ProductSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity.id}

    def update_data(self):
        return {}


class TestProductListView(MontrekListViewTestCase):
    viewname = "product"
    view_class = ProductListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = ProductSatelliteFactory()


class TestProductDeleteView(MontrekDeleteViewTestCase):
    viewname = "product_delete"
    view_class = ProductDeleteView

    def build_factories(self):
        self.sat_obj = ProductSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity.id}
