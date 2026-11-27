import os
import subprocess  # nosec B404 - reads the settings in a fresh interpreter
import sys

from django.conf import settings
from django.test import SimpleTestCase


class TestTestOnlyApps(SimpleTestCase):
    """`settings.py` is read once per process, so each environment is checked in
    a fresh interpreter that only imports the settings."""

    def installed_outside_tests(self, **env: str | None) -> set[str]:
        """The test-only apps installed with `env` applied; a variable given
        as None is removed, so its default applies."""
        environ = os.environ | {"DJANGO_SETTINGS_MODULE": "montrek.settings"}
        environ |= {key: value for key, value in env.items() if value is not None}
        for key in [key for key, value in env.items() if value is None]:
            environ.pop(key, None)
        code = (
            "from django.conf import settings;"
            "print('INSTALLED:' + ','.join(app for app in settings.TEST_ONLY_APPS"
            " if app in settings.INSTALLED_APPS))"
        )
        result = subprocess.run(  # noqa: S603  # nosec B603 - fixed interpreter call
            [sys.executable, "-c", code],
            capture_output=True,
            check=True,
            cwd=settings.BASE_DIR,
            env=environ,
            text=True,
        )
        (line,) = (
            line for line in result.stdout.splitlines() if line.startswith("INSTALLED:")
        )
        return set(filter(None, line.removeprefix("INSTALLED:").split(",")))

    def test_installed_in_tests(self):
        for app in settings.TEST_ONLY_APPS:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_not_an_extension_app(self):
        # The runner overrides MONTREK_EXTENSION_APPS, so read the real list.
        from montrek import settings as settings_module

        self.assertEqual(
            set(settings.TEST_ONLY_APPS) & set(settings_module.MONTREK_EXTENSION_APPS),
            set(),
        )

    def test_test_models_are_test_only(self):
        self.assertIn("baseclasses.testing", settings.TEST_ONLY_APPS)
        self.assertIn("data_import.testing", settings.TEST_ONLY_APPS)

    def test_not_installed_by_default_without_debug(self):
        self.assertEqual(
            self.installed_outside_tests(DEBUG="0", ADD_TEST_ONLY_APPS=None), set()
        )

    def test_installed_by_default_with_debug(self):
        self.assertEqual(
            self.installed_outside_tests(DEBUG="1", ADD_TEST_ONLY_APPS=None),
            set(settings.TEST_ONLY_APPS),
        )

    def test_setting_overrides_debug(self):
        self.assertEqual(
            self.installed_outside_tests(DEBUG="1", ADD_TEST_ONLY_APPS="0"), set()
        )
        self.assertEqual(
            self.installed_outside_tests(DEBUG="0", ADD_TEST_ONLY_APPS="1"),
            set(settings.TEST_ONLY_APPS),
        )
