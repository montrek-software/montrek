"""The `montrek.db_backend` engine and the password provider check.

The wrapper is created from a copy of the test database's settings and never
connects: `get_connection_params()` is what Django passes to each connect.
"""

from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import SimpleTestCase

from montrek.database_settings import check_password_provider
from montrek.db_backend.base import DatabaseWrapper

PROVIDER = f"{__name__}.next_password"
NOT_CALLABLE = f"{__name__}.NOT_A_FUNCTION"
NOT_A_FUNCTION = "a password"

_issued: list[str] = []


def next_password() -> str:
    """A token that changes on every call, like a fresh one each time."""
    _issued.append(f"token-{len(_issued) + 1}")
    return _issued[-1]


class TestPasswordProviderWrapper(SimpleTestCase):
    def wrapper(self, **options):
        settings_dict = {
            **connection.settings_dict,
            "PASSWORD": "",
            "PASSWORD_PROVIDER": PROVIDER,
            "OPTIONS": options,
        }
        return DatabaseWrapper(settings_dict)

    def test_every_connection_gets_a_password_from_the_provider(self):
        wrapper = self.wrapper()
        first = wrapper.get_connection_params()["password"]
        second = wrapper.get_connection_params()["password"]
        self.assertTrue(first.startswith("token-"))
        self.assertNotEqual(first, second)

    def test_the_other_parameters_stay_as_configured(self):
        params = self.wrapper(sslmode="require").get_connection_params()
        self.assertEqual(params["host"], connection.settings_dict["HOST"])
        self.assertEqual(params["user"], connection.settings_dict["USER"])
        self.assertEqual(params["sslmode"], "require")

    def test_a_connection_pool_is_refused(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "does not work with a connection pool"
        ):
            self.wrapper(pool=True).get_connection_params()


class TestCheckPasswordProvider(SimpleTestCase):
    def check_with(self, path):
        with mock.patch.dict(settings.DATABASES["default"], PASSWORD_PROVIDER=path):
            return check_password_provider()

    def test_nothing_to_check_without_a_provider(self):
        self.assertNotIn("PASSWORD_PROVIDER", settings.DATABASES["default"])
        self.assertEqual(check_password_provider(), [])

    def test_an_importable_function_passes(self):
        self.assertEqual(self.check_with(PROVIDER), [])

    def test_a_path_that_cannot_be_imported(self):
        [error] = self.check_with("montrek_example.nowhere.password")
        self.assertEqual(error.id, "montrek.E009")

    def test_a_value_that_is_no_function(self):
        [error] = self.check_with(NOT_CALLABLE)
        self.assertEqual(error.id, "montrek.E010")
