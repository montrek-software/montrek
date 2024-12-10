from django.test import TestCase
from django.core import mail

from api_upload.tests.managers.test_api_upload_manager import MockApiUploadManager
from api_upload.tasks import ApiUploadTask
from testing.decorators.add_logged_in_user import add_logged_in_user


class MockApiUploadTask(ApiUploadTask):
    api_upload_manager_class = MockApiUploadManager


class TestApiUploadTask(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.session_data = {"user_id": self.user.id}

    def test_api_upload_task(self):
        test_task = MockApiUploadTask(session_data=self.session_data)
        test_task.delay()
        self.assertTrue(test_task.upload_result)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
