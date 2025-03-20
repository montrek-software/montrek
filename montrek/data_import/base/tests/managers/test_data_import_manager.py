from django.test import TestCase
from data_import.base.tests.mocks import MockDataImportManager


class TestDataImportManager(TestCase):
    def test_successfull_data_import(self):
        data_import_manager = MockDataImportManager({})
