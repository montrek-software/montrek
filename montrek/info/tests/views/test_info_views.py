from unittest.mock import patch

from info.views.info_views import InfoAdminView, InfoDbStructureView, InfoVersionsView
from testing.test_cases.view_test_cases import MontrekReportViewTestCase


class TestInfoVersionsView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 1
    view_class = InfoVersionsView
    viewname = "info"

    def test_renders_without_git_executable(self):
        with (
            patch(
                "info.managers.info_versions_managers.ReleaseInfo.exists",
                return_value=False,
            ),
            patch("subprocess.check_output", side_effect=FileNotFoundError("git")),
            self.assertLogs("info.modules.git_info", "WARNING"),
        ):
            # The report itself is rendered by the page's HTMX follow-up request.
            response = self.client.get(
                self.url,
                query_params={"state": "loading"},
                headers={"HX-Request": "true"},
            )

        self.assertEqual(response.status_code, 200)


class TestInfoAdminView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 1
    view_class = InfoAdminView
    viewname = "admin"


class TestInfoDbStructureView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 2
    view_class = InfoDbStructureView
    viewname = "db_structure"
