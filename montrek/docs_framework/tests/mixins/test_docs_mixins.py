from django.test import TestCase
from docs_framework.mixins.docs_mixins import DocsFilesMixin


class MockTestClass(DocsFilesMixin): ...


class TestDocsFilesMixin(TestCase):
    def setUp(self):
        self.mixin = MockTestClass()

    def test_get_docs_path(self):
        test_docs_path = self.mixin.get_docs_path()
        dir_end = "/docs_framework/tests/docs"
        self.assertTrue(str(test_docs_path).endswith(dir_end))
