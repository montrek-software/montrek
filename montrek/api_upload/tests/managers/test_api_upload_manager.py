from django.test import TestCase

from api_upload.managers.request_manager import RequestJsonManager
from api_upload.managers.api_upload_manager import ApiUploadManager
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)


class MockRequestManager(RequestJsonManager):
    base_url = "https://api.mock.com/v1/"

    def get_response(self, endpoint: str) -> dict:
        self.status_code = 200
        self.message = "request ok"
        return {"some": "data"}


class MockApiUploadProcessor:
    message = ""

    def __init__(self, upload_registry, session_data):
        self.upload_registry = upload_registry
        self.session_data = session_data

    def pre_check(self, json_response) -> bool:
        self.message = "pre check ok"
        return True

    def process(self, json_response) -> bool:
        self.message = "proccess ok"
        return True

    def post_check(self, json_response) -> bool:
        self.message = "post check ok"
        return True


class MockApiUploadManager(ApiUploadManager):
    endpoint = "endpoint"
    request_manager_class = MockRequestManager
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
            ApiUploadRepository.upload_status.PENDING.value,
        )

    def test_upload_and_process_request_ok(self):
        manager = MockApiUploadManager(session_data=self.session_data)
        upload_result = manager.upload_and_process()

        self.assertTrue(upload_result)
        self.assertEqual(
            manager.api_upload_registry.upload_status,
            ApiUploadRepository.upload_status.PROCESSED.value,
        )
        self.assertEqual(
            manager.messages,
            [
                MontrekMessageInfo("post check ok"),
            ],
        )

    def test_upload_and_process_request_error(self):
        manager = MockApiUploadManager(session_data=self.session_data)

        def get_json_error(endpoint: str) -> dict:
            manager.request_manager.status_code = 0
            manager.request_manager.message = "request error"
            return {}

        manager.request_manager.get_response = get_json_error

        upload_result = manager.upload_and_process()
        api_upload_registry = (
            ApiUploadRepository()
            .receive()
            .filter(pk=manager.api_upload_registry.pk)
            .first()
        )

        self.assertFalse(upload_result)
        self.assertEqual(
            api_upload_registry.upload_status,
            ApiUploadRepository.upload_status.FAILED.value,
        )
        self.assertEqual(
            manager.messages,
            [
                MontrekMessageError("request error"),
            ],
        )

    def test_upload_and_processor_errors(self):
        for method_name in ("pre_check", "process", "post_check"):
            manager = MockApiUploadManager(session_data=self.session_data)
            message = f"{method_name} error"

            def error_method(json_response) -> bool:
                manager.processor.message = message
                return False

            setattr(manager.processor, method_name, error_method)

            upload_result = manager.upload_and_process()
            api_upload_registry = (
                ApiUploadRepository()
                .receive()
                .filter(pk=manager.api_upload_registry.pk)
                .first()
            )
            self.assertFalse(upload_result)
            self.assertEqual(
                api_upload_registry.upload_status,
                ApiUploadRepository.upload_status.FAILED.value,
            )
            self.assertEqual(
                manager.messages,
                [
                    MontrekMessageError(message),
                ],
            )
