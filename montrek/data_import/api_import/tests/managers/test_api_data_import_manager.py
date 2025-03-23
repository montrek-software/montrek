from data_import.base.managers.processor_base import ProcessorBaseABC
from django.test import TestCase
from requesting.managers.request_manager import RequestJsonManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from data_import.api_import.managers.api_data_import_manager import ApiDataImportManager


class MockRequestManager(RequestJsonManager):
    base_url = "https://api.mock.com/v1/"

    def get_response(self, endpoint: str) -> dict:
        self.status_code = 200
        self.message = "request ok"
        return {"some": "data"}


class MockApiDataImportProcessor(ProcessorBaseABC):
    message = ""

    def pre_check(self) -> bool:
        self.message = "pre check ok"
        self.message += self.import_data["some"]
        return True

    def process(self) -> bool:
        self.message = "proccess ok"
        self.message += self.import_data["some"]
        return True

    def post_check(self) -> bool:
        self.message = "post check ok"
        self.message += self.import_data["some"]
        return True


class MockApiDataImportManager(ApiDataImportManager):
    endpoint = "endpoint"
    request_manager_class = MockRequestManager
    api_data_import_processor_class = MockApiDataImportProcessor


class TestApiUploadManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_init_upload(self):
        manager = MockApiDataImportManager(self.session_data)
