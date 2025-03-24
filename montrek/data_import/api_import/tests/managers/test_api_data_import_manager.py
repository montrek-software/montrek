from copy import deepcopy
from django.test import TestCase
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from data_import.api_import.tests.mocks import MockApiDataImportManager



class TestApiUploadManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}
        self.api_data_import_manager = MockApiDataImportManager(self.session_data)

    # def test_setup_registry(self):
    #     test_registry_entry = self.api_data_import_manager.get_registry()
    #     self.assertEqual(test_registry_entry.import_status, "pending")
    #     self.assertEqual(test_registry_entry.import_message, "Initialize Import")
    #     self.assertEqual(
    #         test_registry_entry.import_url, "https://api.mock.com/v1/endpoint"
    #     )
    #
    # def test_process_import_data(self):
    #     self.api_data_import_manager.process_import_data()
    #     test_registry_entry = self.api_data_import_manager.get_registry()
    #     self.assertEqual(test_registry_entry.import_status, "processed")
    #     self.assertEqual(test_registry_entry.import_message, "proccess okdata")
    #
    # def test_process_import_data_json_error(self):
    #     manager = deepcopy(self.api_data_import_manager)
    #
    #     def get_json_error(endpoint: str) -> dict:
    #         manager.request_manager.status_code = 0
    #         manager.request_manager.message = "request error"
    #         return {}
    #
    #     manager.request_manager.get_response = get_json_error
    #     manager.process_import_data()
    #     test_registry_entry = manager.get_registry()
    #     self.assertEqual(test_registry_entry.import_status, "failed")
    #     self.assertEqual(test_registry_entry.import_message, "request error")
