from baseclasses.tests.test_access import RestrictedAppTestCase


class TestStartupChecksSurviveAMalformedApp(RestrictedAppTestCase):
    """The checks must report a malformed app, not die on it."""

    host_app = "montrek_example"
    access_permissions = [object()]  # type: ignore[assignment]  # deliberately malformed

    def test_view_check_reports_instead_of_raising(self):
        from baseclasses.checks import check_restricted_app_views

        with self.assertLogs("baseclasses.access", level="ERROR"):
            errors = check_restricted_app_views()

        # The gated views resolve to the unobtainable permission, which is what
        # E004 reports. That the call returned at all is the point: before the
        # resolver was made to fail closed it raised here.
        self.assertIn("montrek.E004", {error.id for error in errors})
