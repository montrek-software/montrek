from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from sftp.tests.factories.sftp_connection_hub_factories import (
    SftpConnectionHubValueDateFactory,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    SftpConnectionSatelliteFactory,
)
from sftp.views.sftp_connection_views import SftpConnectionCreateView
from sftp.views.sftp_connection_views import SftpConnectionUpdateView
from sftp.views.sftp_connection_views import SftpConnectionListView
from sftp.views.sftp_connection_views import SftpConnectionDeleteView
from sftp.views.sftp_connection_views import SftpConnectionDetailView
from sftp.views.sftp_connection_views import SftpConnectionHistoryView


class TestSftpConnectionCreateView(MontrekCreateViewTestCase):
    viewname = "sftp_connection_create"
    view_class = SftpConnectionCreateView

    def creation_data(self):
        return {}


class TestSftpConnectionUpdateView(MontrekUpdateViewTestCase):
    viewname = "sftp_connection_update"
    view_class = SftpConnectionUpdateView

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {}


class TestSftpConnectionListView(MontrekListViewTestCase):
    viewname = "sftp_connection_list"
    view_class = SftpConnectionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()


class TestSftpConnectionDeleteView(MontrekDeleteViewTestCase):
    viewname = "sftp_connection_delete"
    view_class = SftpConnectionDeleteView

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestSftpConnectionDetailView(MontrekViewTestCase):
    viewname = "sftp_connection_details"
    view_class = SftpConnectionDetailView

    def build_factories(self):
        self.hub_vd = SftpConnectionHubValueDateFactory(value_date=None)
        SftpConnectionSatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}


class TestSftpConnectionHistoryView(MontrekViewTestCase):
    viewname = "sftp_connection_history"
    view_class = SftpConnectionHistoryView

    def build_factories(self):
        self.hub_vd = SftpConnectionHubValueDateFactory(value_date=None)
        SftpConnectionSatelliteFactory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.id}
