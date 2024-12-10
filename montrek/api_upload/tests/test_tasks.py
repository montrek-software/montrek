from django.test import TestCase
from django.core import mail

from api_upload.tests.managers.test_api_upload_manager import MockApiUploadManager
from api_upload.tasks import ApiUploadTask
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestApiUploadTask(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.session_data = {"user_id": self.user.id}

    def test_api_upload_task(self):
        test_task = ApiUploadTask(
            api_upload_manager_class=MockApiUploadManager,
            session_data=self.session_data,
        )
        test_task.delay()
        self.assertTrue(test_task.upload_result)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "API Upload successful")
        self.assertTrue("post check ok" in m.body)

    def test_api_upload_task_fails(self):
        test_task = ApiUploadTask(
            api_upload_manager_class=MockApiUploadManager,
            session_data=self.session_data,
        )
        manager = test_task.api_upload_manager

        def get_json_error(endpoint: str) -> dict:
            manager.request_manager.status_code = 0
            manager.request_manager.message = "request error"
            return {}

        manager.request_manager.get_response = get_json_error
        test_task.delay()
        self.assertFalse(test_task.upload_result)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "API Upload failed")
        self.assertTrue("request error" in m.body)
