from testing.test_cases.view_test_cases import (
    MontrekListViewTestCase,
)
from showcase.factories.sposition_sat_factories import SPositionSatelliteFactory
from showcase.views.sposition_views import SPositionListView


class TestSPositionListView(MontrekListViewTestCase):
    viewname = "sposition_list"
    view_class = SPositionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SPositionSatelliteFactory()
