from django.test import TestCase
from testing.decorators.add_logged_in_user import add_logged_in_user
from data_import.base.tests.mocks import (
    MockDataImportTask,
    MockDataImportTaskFail,
    MockDataImportTaskNoMail,
)
from django.core import mail


class TestDataImportBaseTask(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.test_data = {"test_data": [1, 2, 3]}

    def test_data_import_task(self):
        data_import_task = MockDataImportTask()
        data_import_task.delay({"user_id": self.user.id},self.test_data)
        test_registry_entry = data_import_task.manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "processed")
        self.assertEqual(test_registry_entry.import_message, "Sucessfull Import")
        self.assertEqual(len(mail.outbox), 1)
        test_mail = mail.outbox[0]
        self.assertEqual(test_mail.subject, "Mock Data Import Task successful")
        self.assertTrue("Sucessfull Import" in test_mail.body)

    def test_data_import_task__failure(self):
        data_import_task = MockDataImportTaskFail()
        data_import_task.delay({"user_id": self.user.id},self.test_data)
        test_registry_entry = data_import_task.manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "failed")
        self.assertEqual(test_registry_entry.import_message, "Process Failed")
        self.assertEqual(len(mail.outbox), 1)
        test_mail = mail.outbox[0]
        self.assertEqual(
            test_mail.subject, "ERROR: Mock Data Import Task Fail unsuccessful"
        )
        self.assertTrue("Process Failed" in test_mail.body)

    def test_data_import_task__no_mail(self):
        data_import_task = MockDataImportTaskNoMail()
        data_import_task.delay({"user_id": self.user.id},self.test_data)
        self.assertEqual(len(mail.outbox), 0)
