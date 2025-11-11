from pathlib import Path

from django.test import TestCase
from docs_framework.mixins.docs_mixins import DocsFilesMixin


class MockTestClass(DocsFilesMixin): ...


class MockTestClassNoDocsPath(DocsFilesMixin):
    def get_docs_path(self):
        return Path("unknown/docs")


class TestDocsFilesMixin(TestCase):
    def setUp(self):
        self.mixin = MockTestClass()

    def test_get_docs_path(self):
        test_docs_path = self.mixin.get_docs_path()
        dir_end = "/docs_framework/tests/docs"
        self.assertTrue(str(test_docs_path).endswith(dir_end))

    def test_get_docs_files(self):
        test_docs_files = self.mixin.get_docs_files()
        self.assertEqual(len(test_docs_files), 3)
        files_list = [docfile.docs_name for docfile in test_docs_files]
        self.assertEqual(files_list, ["docs_2", "docs_3", "docs_1"])

    def test_get_docs_files__no_docs_path(self):
        mixin = MockTestClassNoDocsPath()
        test_docs_files = mixin.get_docs_files()
        self.assertEqual(test_docs_files, [])
