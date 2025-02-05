from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from user.tests.factories.montrek_user_hub_factories import (
    MontrekUserHubValueDateFactory,
)
from user.tests.factories.montrek_user_sat_factories import MontrekUserSatelliteFactory
from user.views.montrek_user_views import MontrekUserCreateView
from user.views.montrek_user_views import MontrekUserUpdateView
from user.views.montrek_user_views import MontrekUserListView
from user.views.montrek_user_views import MontrekUserDeleteView
from user.views.montrek_user_views import MontrekUserDetailView


class TestMontrekUserCreateView(MontrekCreateViewTestCase):
    viewname = "montrek_user_create"
    view_class = MontrekUserCreateView

    def creation_data(self):
        return {}


class TestMontrekUserUpdateView(MontrekUpdateViewTestCase):
    viewname = "montrek_user_update"
    view_class = MontrekUserUpdateView

    def build_factories(self):
        self.sat_obj = MontrekUserSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestMontrekUserListView(MontrekListViewTestCase):
    viewname = "montrek_user_list"
    view_class = MontrekUserListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = MontrekUserSatelliteFactory()


class TestMontrekUserDeleteView(MontrekDeleteViewTestCase):
    viewname = "montrek_user_delete"
    view_class = MontrekUserDeleteView

    def build_factories(self):
        self.sat_obj = MontrekUserSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestMontrekUserDetailView(MontrekViewTestCase):
    viewname = "montrek_user_details"
    view_class = MontrekUserDetailView

    def build_factories(self):
        self.hub_vd = MontrekUserHubValueDateFactory(value_date=None)
        MontrekUserSatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}
