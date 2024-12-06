from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.position_sat_factories import PositionSatelliteFactory
from showcase.views.position_views import PositionCreateView
from showcase.views.position_views import PositionUpdateView
from showcase.views.position_views import PositionListView
from showcase.views.position_views import PositionDeleteView


class TestPositionCreateView(MontrekCreateViewTestCase):
    viewname = "position_create"
    view_class = PositionCreateView

    def creation_data(self):
        return {}


class TestPositionUpdateView(MontrekUpdateViewTestCase):
    viewname = "position_update"
    view_class = PositionUpdateView

    def build_factories(self):
        self.sat_obj = PositionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestPositionListView(MontrekListViewTestCase):
    viewname = "position_list"
    view_class = PositionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = PositionSatelliteFactory()


class TestPositionDeleteView(MontrekDeleteViewTestCase):
    viewname = "position_delete"
    view_class = PositionDeleteView

    def build_factories(self):
        self.sat_obj = PositionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
