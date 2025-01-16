import tempfile
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class MontrekTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        with tempfile.TemporaryDirectory() as temp_dir:
            test_settings = {
                "DEBUG": True,
                "MEDIA_ROOT": temp_dir,
                "ADMIN_MAILING_LIST": "test_admin@example.com",
                # Add other test-specific settings here
            }
        self._override = override_settings(**test_settings)
        self._override.enable()

    def teardown_test_environment(self, **kwargs):
        self._override.disable()
        super().teardown_test_environment(**kwargs)
