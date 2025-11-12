from docs_framework.tests.pages.test_docs_pages import DocsPageTest
from docs_framework.views.docs_views import DocsViewABC


class MockDocsView(DocsViewABC):
    page_class = DocsPageTest
