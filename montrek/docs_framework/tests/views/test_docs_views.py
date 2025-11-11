from docs_framework.tests.pages.test_docs_pages import DocsPageTest
from docs_framework.views.docs_views import DocsViewABC
from testing.test_cases.view_test_cases import MontrekReportViewTestCase


class MockDocsView(DocsViewABC):
    page_class = DocsPageTest


class BaseTestDocsViews(MontrekReportViewTestCase):
    view_class = MockDocsView
    viewname = "test_docs"
    expected_number_of_report_elements = 1


class TestDocs1Views(BaseTestDocsViews):
    def url_kwargs(self) -> dict:
        return {"docs_name": "docs_1"}


class TestDocs2Views(BaseTestDocsViews):
    def url_kwargs(self) -> dict:
        return {"docs_name": "docs_2"}
