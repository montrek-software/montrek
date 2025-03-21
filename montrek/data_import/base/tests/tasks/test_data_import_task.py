from django.test import TestCase
from testing.decorators.add_logged_in_user import add_logged_in_user
from data_import.base.tests.mocks import (
    MockDataImportTask,
)


class TestDataImportBaseTask(TestCase):
    @add_logged_in_user
    def test_data_import_task(self):
        test_data = {"test_data": [1, 2, 3]}
        data_import_task = MockDataImportTask({"user_id": self.user.id})
        data_import_task.delay(test_data)
        test_registry_entry = data_import_task.manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "processed")
        self.assertEqual(test_registry_entry.import_message, "Sucessfull Import")
