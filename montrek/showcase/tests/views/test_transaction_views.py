from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.transaction_sat_factories import STransactionSatelliteFactory
from showcase.views.transaction_views import STransactionCreateView
from showcase.views.transaction_views import STransactionUpdateView
from showcase.views.transaction_views import STransactionListView
from showcase.views.transaction_views import STransactionDeleteView


class TestSTransactionCreateView(MontrekCreateViewTestCase):
    viewname = "transaction_create"
    view_class = STransactionCreateView

    def creation_data(self):
        return {}


class TestSTransactionUpdateView(MontrekUpdateViewTestCase):
    viewname = "transaction_update"
    view_class = STransactionUpdateView

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSTransactionListView(MontrekListViewTestCase):
    viewname = "transaction_list"
    view_class = STransactionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory()


class TestSTransactionDeleteView(MontrekDeleteViewTestCase):
    viewname = "transaction_delete"
    view_class = STransactionDeleteView

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
