from django.test import TestCase
from docs_framework.pages.docs_pages import DocsPageABC


class DocsPageTest(DocsPageABC): ...


class TestDocsPage(TestCase):
    def setUp(self):
        self.page = DocsPageTest()

    def test_get_tabs(self):
        tabs = self.page.get_tabs()
        self.assertEqual(len(tabs), 3)
