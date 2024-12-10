from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.scompany_sat_factories import SCompanyStaticSatelliteFactory
from showcase.views.scompany_views import SCompanyCreateView
from showcase.views.scompany_views import SCompanyUpdateView
from showcase.views.scompany_views import SCompanyListView
from showcase.views.scompany_views import SCompanyDeleteView


class TestSCompanyCreateView(MontrekCreateViewTestCase):
    viewname = "scompany_create"
    view_class = SCompanyCreateView

    def creation_data(self):
        return {}


class TestSCompanyUpdateView(MontrekUpdateViewTestCase):
    viewname = "scompany_update"
    view_class = SCompanyUpdateView

    def build_factories(self):
        self.sat_obj = SCompanyStaticSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSCompanyListView(MontrekListViewTestCase):
    viewname = "scompany_list"
    view_class = SCompanyListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SCompanyStaticSatelliteFactory()


class TestSCompanyDeleteView(MontrekDeleteViewTestCase):
    viewname = "scompany_delete"
    view_class = SCompanyDeleteView

    def build_factories(self):
        self.sat_obj = SCompanyStaticSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}
