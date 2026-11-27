import os
import subprocess  # nosec B404 - reads the settings in a fresh interpreter
import sys

from django.conf import settings
from django.test import SimpleTestCase


class TestTestOnlyApps(SimpleTestCase):
    """`settings.py` is read once per process, so each environment is checked in
    a fresh interpreter that only imports the settings."""

    def installed_outside_tests(self, **env: str | None) -> bool:
        """Whether montrek_example is installed with `env` applied; a variable
        given as None is removed, so its default applies."""
        environ = os.environ | {"DJANGO_SETTINGS_MODULE": "montrek.settings"}
        environ |= {key: value for key, value in env.items() if value is not None}
        for key in [key for key, value in env.items() if value is None]:
            environ.pop(key, None)
        code = (
            "from django.conf import settings;"
            "print('montrek_example' in settings.INSTALLED_APPS)"
        )
        result = subprocess.run(  # noqa: S603  # nosec B603 - fixed interpreter call
            [sys.executable, "-c", code],
            capture_output=True,
            check=True,
            cwd=settings.BASE_DIR,
            env=environ,
            text=True,
        )
        return result.stdout.strip().splitlines()[-1] == "True"

    def test_installed_in_tests(self):
        self.assertIn("montrek_example", settings.INSTALLED_APPS)

    def test_not_an_extension_app(self):
        # The runner overrides MONTREK_EXTENSION_APPS, so read the real list.
        from montrek import settings as settings_module

        self.assertNotIn("montrek_example", settings_module.MONTREK_EXTENSION_APPS)

    def test_not_installed_by_default_without_debug(self):
        self.assertFalse(
            self.installed_outside_tests(DEBUG="0", ADD_TEST_ONLY_APPS=None)
        )

    def test_installed_by_default_with_debug(self):
        self.assertTrue(
            self.installed_outside_tests(DEBUG="1", ADD_TEST_ONLY_APPS=None)
        )

    def test_setting_overrides_debug(self):
        self.assertFalse(
            self.installed_outside_tests(DEBUG="1", ADD_TEST_ONLY_APPS="0")
        )
        self.assertTrue(self.installed_outside_tests(DEBUG="0", ADD_TEST_ONLY_APPS="1"))
