from showcase.factories.sproduct_hub_factories import SProductHubValueDateFactory
from showcase.factories.stransaction_hub_factories import (
    LinkSTransactionSProductFactory,
)
from showcase.factories.stransaction_sat_factories import STransactionSatelliteFactory
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekViewTestCase,
)
from showcase.factories.sproduct_sat_factories import SProductSatelliteFactory
from showcase.views.sproduct_views import (
    SProductCreateView,
    SProductDetailView,
    SProductSTransactionListView,
)
from showcase.views.sproduct_views import SProductUpdateView
from showcase.views.sproduct_views import SProductListView
from showcase.views.sproduct_views import SProductDeleteView


class TestSProductCreateView(MontrekCreateViewTestCase):
    viewname = "sproduct_create"
    view_class = SProductCreateView

    def creation_data(self):
        return {"product_name": "Test SProduct", "inception_date": "2021-01-01"}


class TestSProductUpdateView(MontrekUpdateViewTestCase):
    viewname = "sproduct_update"
    view_class = SProductUpdateView

    def build_factories(self):
        self.sat_obj = SProductSatelliteFactory(product_name="Test SProduct")

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {"product_name": "Updated SProduct"}


class TestSProductListView(MontrekListViewTestCase):
    viewname = "showcase"
    view_class = SProductListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SProductSatelliteFactory()


class TestSProductDeleteView(MontrekDeleteViewTestCase):
    viewname = "sproduct_delete"
    view_class = SProductDeleteView

    def build_factories(self):
        self.sat_obj = SProductSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestSProductDetailView(MontrekViewTestCase):
    viewname = "sproduct_details"
    view_class = SProductDetailView

    def build_factories(self):
        self.hub_vd = SProductHubValueDateFactory(value_date=None)
        SProductSatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}


class TestSProductSTransactionListView(MontrekListViewTestCase):
    viewname = "sproduct_stransaction_list"
    view_class = SProductSTransactionListView
    expected_no_of_rows = 1

    def build_factories(self):
        transaction_sat = STransactionSatelliteFactory()
        link_transaction_product = LinkSTransactionSProductFactory(
            hub_in=transaction_sat.hub_entity
        )
        self.product_hub = link_transaction_product.hub_out

    def url_kwargs(self) -> dict:
        return {"pk": self.product_hub.get_hub_value_date().id}


class TestSProductSPositionListView:
    pass
