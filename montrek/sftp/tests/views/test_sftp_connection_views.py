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
    TEST_OLD_PASSWORD,
    TEST_PASSPHRASE,
    TEST_PASSWORD,
    TEST_PRIVATE_KEY,
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
    SftpPrivateKeyCredentialSatelliteFactory,
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
        return {
            "host": "sftp.example.com",
            "port": 2222,
            "user": "alice",
            "host_key_fingerprint": "SHA256:abc",
            "base_path": "/upload",
            "timeout_seconds": 60,
            "auth_method": "password",
            "password": TEST_PASSWORD,
        }

    def additional_assertions(self, created_object):
        self.assertEqual(created_object.password, TEST_PASSWORD)
        self.assertIsNone(created_object.private_key)


class TestSftpConnectionUpdateView(MontrekUpdateViewTestCase):
    viewname = "sftp_connection_update"
    view_class = SftpConnectionUpdateView

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()
        self.credentials = SftpCredentialSatelliteFactory(
            hub_entity=self.sat_obj.hub_entity, password=TEST_OLD_PASSWORD
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {
            "host": "new-sftp.example.com",
            "port": 2022,
            "password": "new-password",
        }

    def test_password_is_not_rendered(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, TEST_OLD_PASSWORD)

    def test_blank_password_keeps_existing_one(self):
        data = self.creation_data()
        data["password"] = ""  # nosec B105 # noqa: S105 : blank on purpose
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self._get_object().password, TEST_OLD_PASSWORD)


class TestSftpConnectionUpdateViewPrivateKey(MontrekUpdateViewTestCase):
    viewname = "sftp_connection_update"
    view_class = SftpConnectionUpdateView

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()
        SftpPrivateKeyCredentialSatelliteFactory(
            hub_entity=self.sat_obj.hub_entity, private_key_passphrase=TEST_PASSPHRASE
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {"host": "new-sftp.example.com"}

    def test_secrets_are_not_rendered(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "OPENSSH PRIVATE KEY")
        self.assertNotContains(response, TEST_PASSPHRASE)

    def test_blank_secrets_keep_existing_ones(self):
        data = self.creation_data()
        data["private_key"] = ""  # nosec B105 # noqa: S105 : blank on purpose
        data["private_key_passphrase"] = (  # nosec B105 # noqa: S105 : blank on purpose
            ""
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        updated = self._get_object()
        self.assertEqual(updated.host, "new-sftp.example.com")
        self.assertEqual(updated.private_key, TEST_PRIVATE_KEY)
        self.assertEqual(updated.private_key_passphrase, TEST_PASSPHRASE)


class TestSftpConnectionListView(MontrekListViewTestCase):
    viewname = "sftp_connection_list"
    view_class = SftpConnectionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = SftpConnectionSatelliteFactory()
        SftpCredentialSatelliteFactory(
            hub_entity=self.sat_obj.hub_entity, password=TEST_PASSWORD
        )

    def test_password_is_not_rendered(self):
        self.assertNotContains(self.response, TEST_PASSWORD)


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
        SftpConnectionSatelliteFactory(
            hub_entity=self.hub_vd.hub, host="sftp.example.com"
        )
        SftpCredentialSatelliteFactory(
            hub_entity=self.hub_vd.hub, password=TEST_PASSWORD
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}

    def test_settings_shown_and_password_masked(self):
        self.assertContains(self.response, "sftp.example.com")
        self.assertNotContains(self.response, TEST_PASSWORD)


class TestSftpConnectionHistoryView(MontrekViewTestCase):
    viewname = "sftp_connection_history"
    view_class = SftpConnectionHistoryView

    def build_factories(self):
        self.hub_vd = SftpConnectionHubValueDateFactory(value_date=None)
        SftpConnectionSatelliteFactory(hub_entity=self.hub_vd.hub)
        SftpCredentialSatelliteFactory(
            hub_entity=self.hub_vd.hub, password=TEST_PASSWORD
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.id}

    def test_password_is_not_rendered(self):
        self.assertNotContains(self.response, TEST_PASSWORD)


class TestSftpConnectionHistoryViewPrivateKey(MontrekViewTestCase):
    viewname = "sftp_connection_history"
    view_class = SftpConnectionHistoryView

    def build_factories(self):
        self.hub_vd = SftpConnectionHubValueDateFactory(value_date=None)
        SftpConnectionSatelliteFactory(hub_entity=self.hub_vd.hub)
        SftpPrivateKeyCredentialSatelliteFactory(
            hub_entity=self.hub_vd.hub, private_key_passphrase=TEST_PASSPHRASE
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.id}

    def test_private_key_and_passphrase_are_not_rendered(self):
        self.assertNotContains(self.response, "OPENSSH PRIVATE KEY")
        self.assertNotContains(self.response, TEST_PASSPHRASE)
