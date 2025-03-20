from django.test import TestCase
from data_import.base.tests.mocks import (
    MockDataImportManager,
    MockDataImportManagerFailPreCheck,
)
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestDataImportManager(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.test_data = {"test_data": [1, 2, 3]}
        self.data_import_manager = MockDataImportManager({"user_id": self.user.id})

    def test_setup_registry(self):
        test_registry_entry = self.data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "pending")
        self.assertEqual(test_registry_entry.import_message, "Initialize Import")

    def test_process_import_data(self):
        self.data_import_manager.process_import_data(self.test_data)
        test_registry_entry = self.data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "processed")
        self.assertEqual(test_registry_entry.import_message, "Sucessfull Import")

    def test_process_import_data__pre_check_fails(self):
        data_import_manager = MockDataImportManagerFailPreCheck(
            {"user_id": self.user.id}
        )
        data_import_manager.process_import_data(self.test_data)
        test_registry_entry = data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "failed")
        self.assertEqual(test_registry_entry.import_message, "Import Failed")
