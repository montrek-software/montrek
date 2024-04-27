from django.test import TestCase

from api_upload.managers.request_manager import RequestManager
from api_upload.managers.api_upload_manager import ApiUploadManager
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRegistryRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)


class MockRequestManager(RequestManager):
    base_url = "https://api.mock.com/v1/"


class MockRequestManagerOk(MockRequestManager):
    def get_json(self, endpoint):
        self.status_code = 200
        self.message = "request ok"
        return {"some": "data"}


class MockRequestManagerError(MockRequestManager):
    def get_json(self, endpoint):
        self.status_code = 0
        self.message = "request error"
        return {}


class MockApiUploadProcessor:
    message = ""

    def __init__(self, upload_registry, session_data):
        self.upload_registry = upload_registry
        self.session_data = session_data

    def pre_check(self, json_response):
        self.message = "pre check ok"
        return True

    def process(self, json_response):
        self.message = "proccess ok"
        return True

    def post_check(self, json_response):
        self.message = "post check ok"
        return True


class MockApiUploadManager(ApiUploadManager):
    endpoint = "endpoint"
    request_manager_class = MockRequestManagerOk
    api_upload_processor_class = MockApiUploadProcessor


class TestApiUploadManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_init_upload(self):
        manager = MockApiUploadManager(self.session_data)
        manager.init_upload()

        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRegistryRepository.upload_status.PENDING.value,
        )

    def test_upload_and_process_request_ok(self):
        manager_class = MockApiUploadManager
        manager_class.request_manager_class = MockRequestManagerOk
        manager = manager_class(session_data=self.session_data)
        upload_result = manager.upload_and_process()

        self.assertTrue(upload_result)
        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRegistryRepository.upload_status.PROCESSED.value,
        )
        self.assertEqual(
            manager.messages,
            [
                MontrekMessageInfo("post check ok"),
            ],
        )

    def test_upload_and_process_request_error(self):
        manager_class = MockApiUploadManager
        manager_class.request_manager_class = MockRequestManagerError
        manager = manager_class(session_data=self.session_data)
        upload_result = manager.upload_and_process()

        self.assertFalse(upload_result)
        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRegistryRepository.upload_status.FAILED.value,
        )
        self.assertEqual(
            manager.messages,
            [
                MontrekMessageError("request error"),
            ],
        )
