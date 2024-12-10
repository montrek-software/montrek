from django.test import TestCase
from django.core import mail

from api_upload.tests.managers.test_api_upload_manager import (
    MockApiUploadManager,
    MockApiUploadManagerFail,
)
from api_upload.tasks import ApiUploadTask
from testing.decorators.add_logged_in_user import add_logged_in_user


class MockApiUploadTask(ApiUploadTask):
    api_upload_manager_class = MockApiUploadManager


class MockApiUploadTaskFail(ApiUploadTask):
    api_upload_manager_class = MockApiUploadManagerFail


class TestApiUploadTask(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.session_data = {"user_id": self.user.id}

    def test_api_upload_task(self):
        test_task = MockApiUploadTask()
        test_task.delay(
            session_data=self.session_data,
        )
        self.assertTrue(test_task.upload_result)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "API Upload successful")
        self.assertTrue("post check ok" in m.body)
        self.assertTrue(
            "<i>API: <a href='https://api.mock.com/v1/endpoint'>https://api.mock.com/v1/endpoint</a></i>"
            in m.body
        )

    def test_api_upload_task_fails(self):
        test_task = MockApiUploadTaskFail()
        test_task.delay(
            session_data=self.session_data,
        )
        self.assertFalse(test_task.upload_result)
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "API Upload failed")
        self.assertTrue("process not ok" in m.body)
