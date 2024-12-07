from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.sposition_sat_factories import SPositionSatelliteFactory
from showcase.views.sposition_views import SPositionCreateView
from showcase.views.sposition_views import SPositionUpdateView
from showcase.views.sposition_views import SPositionListView
from showcase.views.sposition_views import SPositionDeleteView


class TestSPositionCreateView(MontrekCreateViewTestCase):
    viewname = "sposition_create"
    view_class = SPositionCreateView

    def creation_data(self):
        return {}


class TestSPositionUpdateView(MontrekUpdateViewTestCase):
    viewname = "sposition_update"
    view_class = SPositionUpdateView

    def build_factories(self):
        self.sat_obj = SPositionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSPositionListView(MontrekListViewTestCase):
    viewname = "sposition_list"
    view_class = SPositionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SPositionSatelliteFactory()


class TestSPositionDeleteView(MontrekDeleteViewTestCase):
    viewname = "sposition_delete"
    view_class = SPositionDeleteView

    def build_factories(self):
        self.sat_obj = SPositionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
