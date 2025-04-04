from testing.test_cases.view_test_cases import MontrekReportViewTestCase
from info.tests.mocks import MockInfoVersionsView


class TestInfoVersionsView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 1
    view_class = MockInfoVersionsView
    viewname = "info"
