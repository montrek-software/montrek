from django.test import TestCase

from api_upload.tests.managers.test_api_upload_manager import MockApiUploadManager
from api_upload.tasks import ApiUploadTask


class MockApiUploadTask(ApiUploadTask):
    api_upload_manager_class = MockApiUploadManager


class TestApiUploadTask(TestCase):
    def test_api_upload_task(self):
        ApiUploadTask().delay()
