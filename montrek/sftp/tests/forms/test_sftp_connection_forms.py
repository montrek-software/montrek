from django.test import TestCase

from sftp.forms.sftp_connection_forms import SftpConnectionCreateForm
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository
from sftp.tests.factories.sftp_connection_sat_factories import (
    TEST_HOST_FINGERPRINT,
    TEST_PASSWORD,
    TEST_PRIVATE_KEY,
)

CONNECTION_DATA = {
    "host": "sftp.example.com",
    "port": 22,
    "user": "alice",
    "host_key_fingerprint": TEST_HOST_FINGERPRINT,
    "base_path": "/",
    "timeout_seconds": 30,
}


class TestSftpConnectionCreateForm(TestCase):
    def _form(self, data: dict, initial: dict | None = None):
        return SftpConnectionCreateForm(
            repository=SftpConnectionRepository(),
            data=CONNECTION_DATA | data,
            initial=initial or {},
        )

    def test_password_auth_with_password_is_valid(self):
        form = self._form({"auth_method": "password", "password": TEST_PASSWORD})
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_auth_requires_password(self):
        form = self._form({"auth_method": "password"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["password"], ["Required for password authentication."]
        )

    def test_private_key_auth_with_key_is_valid(self):
        form = self._form(
            {"auth_method": "private_key", "private_key": TEST_PRIVATE_KEY}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_private_key_auth_requires_private_key(self):
        form = self._form({"auth_method": "private_key", "password": TEST_PASSWORD})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["private_key"], ["Required for key authentication."]
        )

    def test_blank_secret_on_update_uses_existing_value(self):
        form = self._form(
            {"auth_method": "password", "password": ""},
            initial={"password": TEST_PASSWORD},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["password"], TEST_PASSWORD)

    def test_switching_to_key_auth_on_update_requires_key(self):
        form = self._form(
            {"auth_method": "private_key", "password": ""},
            initial={"password": TEST_PASSWORD},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("private_key", form.errors)


class TestSftpConnectionCreateFormHostKey(TestCase):
    def _form(self, fingerprint: str | None, trusted_host: bool = False):
        data = CONNECTION_DATA | {
            "auth_method": "password",
            "password": TEST_PASSWORD,
            "trusted_host": trusted_host,
        }
        if fingerprint is None:
            del data["host_key_fingerprint"]
        else:
            data["host_key_fingerprint"] = fingerprint
        return SftpConnectionCreateForm(
            repository=SftpConnectionRepository(), data=data
        )

    def test_fingerprint_is_required(self):
        for fingerprint in (None, ""):
            with self.subTest(fingerprint=fingerprint):
                form = self._form(fingerprint)
                self.assertFalse(form.is_valid())
                self.assertIn("host_key_fingerprint", form.errors)

    def test_accepts_sha256_fingerprint_with_or_without_prefix(self):
        for fingerprint in (
            TEST_HOST_FINGERPRINT,
            TEST_HOST_FINGERPRINT.removeprefix("SHA256:"),
            f"{TEST_HOST_FINGERPRINT}=",
        ):
            with self.subTest(fingerprint=fingerprint):
                form = self._form(fingerprint)
                self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_malformed_fingerprint(self):
        for fingerprint in (
            "SHA256:abc",
            "MD5:16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48",
            f"{TEST_HOST_FINGERPRINT}x",
        ):
            with self.subTest(fingerprint=fingerprint):
                form = self._form(fingerprint)
                self.assertFalse(form.is_valid())
                self.assertIn("SHA256 fingerprint", str(form.errors))

    def test_trusted_host_needs_no_fingerprint(self):
        for fingerprint in (None, ""):
            with self.subTest(fingerprint=fingerprint):
                form = self._form(fingerprint, trusted_host=True)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertTrue(form.cleaned_data["trusted_host"])

    def test_trusted_host_still_rejects_malformed_fingerprint(self):
        form = self._form("SHA256:abc", trusted_host=True)
        self.assertFalse(form.is_valid())
        self.assertIn("SHA256 fingerprint", str(form.errors))

    def test_missing_fingerprint_explains_trusted_host(self):
        form = self._form(None)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["host_key_fingerprint"],
            ["Required unless the host is trusted."],
        )

    def test_malformed_fingerprint_is_reported_once(self):
        form = self._form("SHA256:abc")
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors["host_key_fingerprint"]), 1)
