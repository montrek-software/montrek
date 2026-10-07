from django.test import TestCase

from sftp.managers.sftp_connection_managers import (
    SftpConnectionDetailsManager,
    SftpConnectionTableManager,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    TEST_HOST_FINGERPRINT,
    TEST_PASSPHRASE,
    TEST_PASSWORD,
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
    SftpPrivateKeyCredentialSatelliteFactory,
)


class TestSftpConnectionTableManager(TestCase):
    def setUp(self):
        self.connection = SftpConnectionSatelliteFactory(
            host="sftp.example.com", port=2222, user="alice", base_path="/in"
        )
        self.credentials = SftpCredentialSatelliteFactory(
            hub_entity=self.connection.hub_entity, password=TEST_PASSWORD
        )
        self.manager = SftpConnectionTableManager({})

    def test_table_contains_connection_settings(self):
        table = self.manager.get_full_table()
        self.assertEqual(table.count(), 1)
        row = table.get()
        self.assertEqual(row.host, "sftp.example.com")
        self.assertEqual(row.port, 2222)
        self.assertEqual(row.user, "alice")
        self.assertEqual(row.base_path, "/in")
        self.assertEqual(row.auth_method, "password")

    def test_table_elements(self):
        names = [element.name for element in self.manager.table_elements]
        self.assertEqual(
            names,
            [
                "Details",
                "Host",
                "Port",
                "User",
                "Base Path",
                "Auth Method",
                "Edit",
                "Delete",
            ],
        )

    def test_html_shows_settings_but_no_secrets(self):
        html = self.manager.to_html()
        self.assertIn("sftp.example.com", html)
        self.assertIn("alice", html)
        self.assertNotIn(TEST_PASSWORD, html)

    def test_df_contains_no_secrets(self):
        df = self.manager.get_df()
        self.assertEqual(df["Host"].tolist(), ["sftp.example.com"])
        self.assertNotIn("Password", df.columns)
        self.assertFalse(df.isin([TEST_PASSWORD]).any().any())


class TestSftpConnectionDetailsManager(TestCase):
    def _manager(self, hub) -> SftpConnectionDetailsManager:
        return SftpConnectionDetailsManager({"pk": hub.pk})

    def test_details_show_settings_and_mask_password(self):
        connection = SftpConnectionSatelliteFactory(
            host="sftp.example.com",
            user="alice",
            host_key_fingerprint=TEST_HOST_FINGERPRINT,
            timeout_seconds=45,
        )
        SftpCredentialSatelliteFactory(
            hub_entity=connection.hub_entity, password=TEST_PASSWORD
        )

        html = self._manager(connection.hub_entity).to_html()

        self.assertIn("sftp.example.com", html)
        self.assertIn("alice", html)
        self.assertIn(TEST_HOST_FINGERPRINT, html)
        self.assertIn("45", html)
        self.assertIn("*" * len(TEST_PASSWORD), html)
        self.assertNotIn(TEST_PASSWORD, html)

    def test_details_mask_private_key_and_passphrase(self):
        connection = SftpConnectionSatelliteFactory()
        credentials = SftpPrivateKeyCredentialSatelliteFactory(
            hub_entity=connection.hub_entity,
            private_key_passphrase=TEST_PASSPHRASE,
        )

        html = self._manager(connection.hub_entity).to_html()

        self.assertIn("private_key", html)
        self.assertNotIn("OPENSSH PRIVATE KEY", html)
        self.assertNotIn(credentials.private_key, html)
        self.assertNotIn(TEST_PASSPHRASE, html)

    def test_details_without_credentials(self):
        connection = SftpConnectionSatelliteFactory(host="sftp.example.com")

        manager = self._manager(connection.hub_entity)
        fields = {
            field.name: field.display_value.strip()
            for row in manager.get_details_data()
            for field in row
        }

        self.assertIn("sftp.example.com", manager.to_html())
        self.assertEqual(fields["Password"], "")
        self.assertEqual(fields["Private Key"], "")
        self.assertEqual(fields["Private Key Passphrase"], "")
