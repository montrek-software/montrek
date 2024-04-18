from django.test.runner import DiscoverRunner


class MontrekTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        kwargs["settings"] = "montrek.settings.test_settings"
        super().__init__(*args, **kwargs)
