from docs_framework.tests.pages.test_docs_pages import DocsPageTest
from docs_framework.views.docs_views import DocsViewABC
from testing.test_cases.view_test_cases import MontrekReportViewTestCase


class MockDocsView(DocsViewABC):
    page_class = DocsPageTest


class TestDocs1Views(MontrekReportViewTestCase):
    view_class = MockDocsView
    viewname = "test_docs"
    expected_number_of_report_elements = 1

    def url_kwargs(self) -> dict:
        return {"docs_name": "docs_1"}
