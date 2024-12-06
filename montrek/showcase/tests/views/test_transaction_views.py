from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.transaction_sat_factories import TransactionSatelliteFactory
from showcase.views.transaction_views import TransactionCreateView
from showcase.views.transaction_views import TransactionUpdateView
from showcase.views.transaction_views import TransactionListView
from showcase.views.transaction_views import TransactionDeleteView


class TestTransactionCreateView(MontrekCreateViewTestCase):
    viewname = "transaction_create"
    view_class = TransactionCreateView

    def creation_data(self):
        return {}


class TestTransactionUpdateView(MontrekUpdateViewTestCase):
    viewname = "transaction_update"
    view_class = TransactionUpdateView

    def build_factories(self):
        self.sat_obj = TransactionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestTransactionListView(MontrekListViewTestCase):
    viewname = "transaction_list"
    view_class = TransactionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = TransactionSatelliteFactory()


class TestTransactionDeleteView(MontrekDeleteViewTestCase):
    viewname = "transaction_delete"
    view_class = TransactionDeleteView

    def build_factories(self):
        self.sat_obj = TransactionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
