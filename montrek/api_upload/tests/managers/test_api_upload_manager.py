from django.test import TestCase

from api_upload.managers.request_manager import RequestManager
from api_upload.managers.api_upload_manager import ApiUploadManager
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRegistryRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class MockRequestManager(RequestManager):
    base_url = "https://api.mock.com/v1/"

    def get_json(self, endpoint):
        self.status_code = 200
        return {"data": "mock data"}


class MockApiUploadProcessor:
    message = ""

    def __init__(self, upload_registry, session_data):
        self.upload_registry = upload_registry
        self.session_data = session_data

    def pre_check(self, json_response):
        return True

    def process(self, json_response):
        return True

    def post_check(self, json_response):
        return True


class MockApiUploadManager(ApiUploadManager):
    endpoint = "endpoint"
    request_manager_class = MockRequestManager
    api_upload_processor_class = MockApiUploadProcessor


class TestApiUploadManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_upload_and_process(self):
        # todo: extend test
        manager = MockApiUploadManager(session_data=self.session_data)

        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRegistryRepository.upload_status.PENDING.value,
        )
        upload_result = manager.upload_and_process()
        self.assertTrue(upload_result)
        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRegistryRepository.upload_status.PROCESSED.value,
        )
