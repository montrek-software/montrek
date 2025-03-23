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
        self.api_data_import_manager = MockApiDataImportManager(self.session_data)

    def test_setup_registry(self):
        test_registry_entry = self.api_data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "pending")
        self.assertEqual(test_registry_entry.import_message, "Initialize Import")

    def test_process_import_data(self):
        self.api_data_import_manager.process_import_data(self.test_data)
        test_registry_entry = self.api_data_import_manager.get_registry()
        self.assertEqual(test_registry_entry.import_status, "processed")
        self.assertEqual(test_registry_entry.import_message, "Sucessfull Import")
