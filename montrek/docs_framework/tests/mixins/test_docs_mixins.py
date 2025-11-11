import os
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
        files_list = [str(docfile).split(os.sep)[-1] for docfile in test_docs_files]
        files_list.sort()
        self.assertEqual(files_list, ["docs_1.md", "docs_2.md", "docs_3.md"])

    def test_get_docs_files__no_docs_path(self):
        mixin = MockTestClassNoDocsPath()
        test_docs_files = mixin.get_docs_files()
        self.assertEqual(test_docs_files, [])
