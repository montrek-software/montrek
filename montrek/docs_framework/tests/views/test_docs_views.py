from docs_framework.tests.views.mock_views import MockDocsView
from testing.test_cases.view_test_cases import MontrekReportViewTestCase


class TestDocs1Views(MontrekReportViewTestCase):
    view_class = MockDocsView
    viewname = "test_docs"
    expected_number_of_report_elements = 1

    def url_kwargs(self) -> dict:
        return {"docs_name": "docs_1"}
