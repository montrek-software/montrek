from django.test import TestCase
from file_upload.managers.file_upload_manager_mixins import (
    ExcelLogFileMixin,
)


class MockUploadRegistryHub:
    ...


class MockNoLinkNameProcessor(ExcelLogFileMixin):
    def __init__(self):
        self.file_upload_registry_hub = MockUploadRegistryHub()


class MockNoSessionDataProcessor(ExcelLogFileMixin):
    log_link_name = "Test"

    def __init__(self):
        self.file_upload_registry_hub = MockUploadRegistryHub()


class TestExcelLogFileMixin(TestCase):
    def test_log_excel_file__no_registry(self):
        with self.assertRaises(AttributeError) as e:
            ExcelLogFileMixin().generate_log_file_excel("Fails")
        self.assertEqual(
            str(e.exception),
            "ExcelLogFileMixin has no file_upload_registry_hub attribute.",
        )

    def test_log_excel_file__no_log_link_name(self):
        with self.assertRaises(AttributeError) as e:
            MockNoLinkNameProcessor().generate_log_file_excel("Fails")
        self.assertEqual(
            str(e.exception),
            "ExcelLogFileMixin has no log_link_name attribute.",
        )

    def test_log_excel_file__no_session_data(self):
        with self.assertRaises(AttributeError) as e:
            MockNoSessionDataProcessor().generate_log_file_excel("Fails")
        self.assertEqual(
            str(e.exception),
            "ExcelLogFileMixin has no session_data attribute.",
        )
