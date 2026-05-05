import unittest

from data_import.api_import.managers.api_data_import_processor import (
    ApiDataImportProcessorBase,
)
from requesting.managers.request_manager import RequestJsonManager

SESSION_DATA = {}
ENDPOINT = "items/"
BASE_URL = "https://api.mock.com/v1/"
RESPONSE_DATA = {"id": 1, "name": "test"}


# ---- mock request managers ----


class MockRequestManager(RequestJsonManager):
    base_url = BASE_URL

    def get_response(self, endpoint: str) -> dict:
        self.status_code = 200
        self.message = "OK"
        return RESPONSE_DATA


class MockConnectionFailRequestManager(MockRequestManager):
    def get_response(self, endpoint: str) -> dict:
        self.status_code = 0
        self.message = "Connection failed"
        return {}


class MockUnauthorizedRequestManager(MockRequestManager):
    def get_response(self, endpoint: str) -> dict:
        self.status_code = 401
        self.message = "401 Client Error: Unauthorized"
        return {}


# ---- concrete test processors ----


class ConcreteProcessor(ApiDataImportProcessorBase):
    request_manager_class = MockRequestManager
    endpoint = ENDPOINT

    def apply_import_data(self) -> bool:
        self.set_message("Import successful")
        return True

    def post_check(self) -> bool:
        return True


class ConcreteFailApplyProcessor(ConcreteProcessor):
    def apply_import_data(self) -> bool:
        self.set_message("Apply failed")
        return False


# ---- tests ----


class TestApiDataImportProcessorBaseInit(unittest.TestCase):
    def setUp(self):
        self.processor = ConcreteProcessor(SESSION_DATA, {"already": "fetched"})

    def test_import_data_is_none_regardless_of_passed_value(self):
        # import_data is always fetched from the API in pre_check, never from the constructor
        self.assertIsNone(self.processor.import_data)

    def test_request_manager_is_instantiated(self):
        self.assertIsInstance(self.processor.request_manager, MockRequestManager)

    def test_message_is_empty_on_init(self):
        self.assertEqual(self.processor.message, "")

    def test_send_mail_is_true_by_default(self):
        self.assertTrue(self.processor.send_mail)


class TestApiDataImportProcessorPreCheck(unittest.TestCase):
    def test_returns_true_on_200(self):
        processor = ConcreteProcessor(SESSION_DATA, {})
        self.assertTrue(processor.pre_check())

    def test_populates_import_data_on_success(self):
        processor = ConcreteProcessor(SESSION_DATA, {})
        processor.pre_check()
        self.assertEqual(processor.import_data, RESPONSE_DATA)

    def test_returns_false_on_connection_failure(self):
        class Processor(ConcreteProcessor):
            request_manager_class = MockConnectionFailRequestManager

        self.assertFalse(Processor(SESSION_DATA, {}).pre_check())

    def test_sets_message_from_request_manager_on_connection_failure(self):
        class Processor(ConcreteProcessor):
            request_manager_class = MockConnectionFailRequestManager

        processor = Processor(SESSION_DATA, {})
        processor.pre_check()
        self.assertEqual(processor.message, "Connection failed")

    def test_returns_false_on_401(self):
        class Processor(ConcreteProcessor):
            request_manager_class = MockUnauthorizedRequestManager

        self.assertFalse(Processor(SESSION_DATA, {}).pre_check())

    def test_sets_message_from_request_manager_on_401(self):
        class Processor(ConcreteProcessor):
            request_manager_class = MockUnauthorizedRequestManager

        processor = Processor(SESSION_DATA, {})
        processor.pre_check()
        self.assertEqual(processor.message, "401 Client Error: Unauthorized")


class TestApiDataImportProcessorReadImportData(unittest.TestCase):
    def test_populates_import_data_from_response(self):
        processor = ConcreteProcessor(SESSION_DATA, {})
        processor._read_import_data()
        self.assertEqual(processor.import_data, RESPONSE_DATA)

    def test_calls_correct_endpoint(self):
        called_with = []

        class TrackingRequestManager(MockRequestManager):
            def get_response(self, endpoint: str) -> dict:
                called_with.append(endpoint)
                return super().get_response(endpoint)

        class TrackingProcessor(ConcreteProcessor):
            request_manager_class = TrackingRequestManager

        TrackingProcessor(SESSION_DATA, {})._read_import_data()
        self.assertEqual(called_with, [ENDPOINT])


class TestApiDataImportProcessorProcess(unittest.TestCase):
    def _processor_after_pre_check(self, processor_class=ConcreteProcessor):
        processor = processor_class(SESSION_DATA, {})
        processor.pre_check()
        return processor

    def test_returns_true_when_apply_import_data_succeeds(self):
        self.assertTrue(self._processor_after_pre_check().process())

    def test_returns_false_when_apply_import_data_fails(self):
        self.assertFalse(
            self._processor_after_pre_check(ConcreteFailApplyProcessor).process()
        )

    def test_sets_message_on_success(self):
        processor = self._processor_after_pre_check()
        processor.process()
        self.assertEqual(processor.message, "Import successful")

    def test_sets_message_on_failure(self):
        processor = self._processor_after_pre_check(ConcreteFailApplyProcessor)
        processor.process()
        self.assertEqual(processor.message, "Apply failed")

    def test_apply_import_data_not_implemented_raises(self):
        class ProcessorWithoutApply(ApiDataImportProcessorBase):
            request_manager_class = MockRequestManager
            endpoint = ENDPOINT

            def post_check(self) -> bool:
                return True

        processor = ProcessorWithoutApply(SESSION_DATA, {})
        with self.assertRaises(NotImplementedError):
            processor.process()


class TestApiDataImportProcessorPostCheck(unittest.TestCase):
    def test_post_check_not_implemented_on_base_raises(self):
        class ProcessorWithoutPostCheck(ApiDataImportProcessorBase):
            request_manager_class = MockRequestManager
            endpoint = ENDPOINT

            def apply_import_data(self) -> bool:
                return True

        with self.assertRaises(NotImplementedError):
            ProcessorWithoutPostCheck(SESSION_DATA, {}).post_check()


class TestApiDataImportProcessorGetEndpointUrl(unittest.TestCase):
    def test_returns_base_url_plus_endpoint(self):
        processor = ConcreteProcessor(SESSION_DATA, {})
        self.assertEqual(processor.get_endpoint_url(), f"{BASE_URL}{ENDPOINT}")
