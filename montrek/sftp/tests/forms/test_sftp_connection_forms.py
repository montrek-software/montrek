from django.test import TestCase

from sftp.forms.sftp_connection_forms import SftpConnectionCreateForm
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository
from sftp.tests.factories.sftp_connection_sat_factories import (
    TEST_PASSWORD,
    TEST_PRIVATE_KEY,
)

CONNECTION_DATA = {
    "host": "sftp.example.com",
    "port": 22,
    "user": "alice",
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
