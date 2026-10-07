from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase

from sftp.models.sftp_connection_sat_models import (
    SftpConnectionSatellite,
    SftpCredentialSatellite,
)
from sftp.tests.factories.sftp_connection_hub_factories import SftpConnectionHubFactory
from sftp.tests.factories.sftp_connection_sat_factories import (
    TEST_HOST_FINGERPRINT,
    TEST_PASSPHRASE,
    TEST_PASSWORD,
    TEST_PRIVATE_KEY,
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
    SftpPrivateKeyCredentialSatelliteFactory,
)


class TestSftpConnectionSatellite(TestCase):
    def test_str(self):
        connection = SftpConnectionSatelliteFactory(
            host="sftp.example.com", port=2222, user="alice"
        )
        self.assertEqual(str(connection), "alice@sftp.example.com:2222")

    def test_trusted_host_defaults_to_false(self):
        self.assertFalse(SftpConnectionSatellite().trusted_host)

    def test_clean_with_fingerprint(self):
        SftpConnectionSatellite(host_key_fingerprint=TEST_HOST_FINGERPRINT).clean()

    def test_clean_requires_fingerprint_unless_trusted(self):
        with self.assertRaises(ValidationError) as context:
            SftpConnectionSatellite(host_key_fingerprint="").clean()
        self.assertIn("host_key_fingerprint", context.exception.message_dict)

    def test_clean_trusted_host_without_fingerprint(self):
        SftpConnectionSatellite(host_key_fingerprint="", trusted_host=True).clean()


class TestSftpCredentialSatellite(TestCase):
    def setUp(self):
        self.hub = SftpConnectionHubFactory()

    def test_str_does_not_render_secrets(self):
        credentials = SftpCredentialSatelliteFactory(
            hub_entity=self.hub, password=TEST_PASSWORD
        )
        self.assertEqual(
            str(credentials), f"Credentials (Password) for hub {self.hub.id}"
        )

    def test_secrets_are_encrypted_at_rest(self):
        SftpPrivateKeyCredentialSatelliteFactory(
            hub_entity=self.hub, private_key_passphrase=TEST_PASSPHRASE
        )
        # Read the columns bypassing the ORM, which would decrypt them
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT private_key, private_key_passphrase FROM "  # nosec B608
                f"{SftpCredentialSatellite._meta.db_table}"
            )
            raw = cursor.fetchone()
        stored = SftpCredentialSatellite.objects.get()
        self.assertNotIn("PRIVATE KEY", raw[0])
        self.assertNotEqual(raw[1], TEST_PASSPHRASE)
        self.assertEqual(stored.private_key_passphrase, TEST_PASSPHRASE)

    def test_empty_secrets_are_stored_as_null(self):
        SftpCredentialSatelliteFactory(hub_entity=self.hub)
        stored = SftpCredentialSatellite.objects.get()
        self.assertIsNone(stored.private_key)
        self.assertIsNone(stored.private_key_passphrase)

    def test_clean_password_auth(self):
        SftpCredentialSatellite(
            hub_entity=self.hub,
            auth_method=SftpCredentialSatellite.AuthMethod.PASSWORD,
            password=TEST_PASSWORD,
        ).clean()

    def test_clean_password_auth_requires_password(self):
        credentials = SftpCredentialSatellite(
            hub_entity=self.hub,
            auth_method=SftpCredentialSatellite.AuthMethod.PASSWORD,
        )
        with self.assertRaises(ValidationError) as context:
            credentials.clean()
        self.assertIn("password", context.exception.message_dict)

    def test_clean_private_key_auth(self):
        SftpCredentialSatellite(
            hub_entity=self.hub,
            auth_method=SftpCredentialSatellite.AuthMethod.PRIVATE_KEY,
            private_key=TEST_PRIVATE_KEY,
        ).clean()

    def test_clean_private_key_auth_requires_private_key(self):
        credentials = SftpCredentialSatellite(
            hub_entity=self.hub,
            auth_method=SftpCredentialSatellite.AuthMethod.PRIVATE_KEY,
            password=TEST_PASSWORD,
        )
        with self.assertRaises(ValidationError) as context:
            credentials.clean()
        self.assertIn("private_key", context.exception.message_dict)
