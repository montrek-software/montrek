from django.test import TestCase
from data_import.base.tests.mocks import MockDataImportManager
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestDataImportManager(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.test_data = {"test_data": [1, 2, 3]}
        self.data_import_manager = MockDataImportManager({"user_id": self.user.id})

    def test_setup_registry(self):
        test_registry_entry = self.data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "pending")

    def test_set_import_data(self):
        self.assertEqual(self.data_import_manager.import_data, None)
        self.data_import_manager.set_import_data(self.test_data)
        self.assertEqual(self.data_import_manager.import_data, self.test_data)

    def test_process_import_data(self):
        self.data_import_manager.set_import_data(self.test_data)
        self.data_import_manager.process_import_data(self.test_data)
