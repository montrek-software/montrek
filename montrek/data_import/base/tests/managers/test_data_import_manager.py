from django.test import TestCase
from data_import.base.tests.mocks import MockDataImportManager


class TestDataImportManager(TestCase):
    def test_set_import_data(self):
        data_import_manager = MockDataImportManager({})
        self.assertEqual(data_import_manager.import_data, None)
        test_data = {"test_data": [1, 2, 3]}
        data_import_manager.set_import_data(test_data)
        self.assertEqual(data_import_manager.import_data, test_data)
