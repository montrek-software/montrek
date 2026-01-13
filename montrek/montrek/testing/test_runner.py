import tempfile
import socket

from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings
from django.urls import reverse_lazy

_real_create_connection = socket.create_connection


class MontrekTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        with tempfile.TemporaryDirectory() as temp_dir:
            test_settings = {
                "IS_TEST_RUN": True,
                "DEBUG": True,
                "MEDIA_ROOT": temp_dir,
                "HOME_URL": "home",
                "NAVBAR_HOME_URL": "home",
                "ADMIN_MAILING_LIST": "test_admin@example.com",
                "CELERY_TASK_ALWAYS_EAGER": 1,
                "CELERY_TASK_EAGER_PROPAGATES": 1,
                "NAVBAR_APPS": [
                    "mailing",
                    "info",
                    "montrek_example.montrek_example_report",
                    "",
                ],
                "NAVBAR_RENAME": {"info": "Amazing App"},
                "MONTREK_EXTENSION_APPS": ["app1", "app2", "mt_dummy.app3"],
                "ENABLE_KEYCLOAK": False,
                "LOGIN_URL": reverse_lazy("login"),
                "AUTHENTICATION_BACKENDS": (
                    "django.contrib.auth.backends.ModelBackend",
                ),
                # Add other test-specific settings here
                "ADMIN_NAME": "test_admin",
                "ADMIN_EMAIL": "test@admin.de",
                "ADMIN_PASSWORD": "testpassword",
                "CLIENT_LOGO_PATH": "montrek_logo_variant.png",
                "MIDDLEWARE": [
                    m
                    for m in settings.MIDDLEWARE
                    if m != "querycount.middleware.QueryCountMiddleware"
                ],
            }
        self._override = override_settings(**test_settings)
        self._override.enable()
        socket.create_connection = self._guarded_create_connection

    def teardown_test_environment(self, **kwargs):
        self._override.disable()
        super().teardown_test_environment(**kwargs)

    def _guarded_create_connection(self, address, *args, **kwargs):
        host, *_ = address

        if host in ("127.0.0.1", "localhost", "::1"):
            return _real_create_connection(address, *args, **kwargs)

        raise RuntimeError("External network access is forbidden during tests")
