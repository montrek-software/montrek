from testing.test_cases.view_test_cases import MontrekReportViewTestCase
from info.views.info_views import InfoVersionsView, InfoAdminView


class TestInfoVersionsView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 1
    view_class = InfoVersionsView
    viewname = "info"


class TestInfoAdminView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 1
    view_class = InfoAdminView
    viewname = "admin"
