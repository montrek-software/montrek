import pandas as pd
from django.test import TestCase
from django.utils import timezone
from file_upload.managers.file_upload_manager_mixins import (
    LogFileMixin,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryHubFactory,
)
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.tests.utils import LogFileTestMixin
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class MockUploadRegistryHub:
    ...


class MockNoLinkNameProcessor(LogFileMixin):
    def __init__(self):
        self.file_upload_registry_hub = MockUploadRegistryHub()


class MockNoSessionDataProcessor(LogFileMixin):
    log_link_name = "Test"

    def __init__(self):
        self.file_upload_registry_hub = MockUploadRegistryHub()


class MockDataProcessor(LogFileMixin):
    def __init__(self):
        self.file_upload_registry_hub = FileUploadRegistryHubFactory.create()


class MockRegistryRepository:
    def __init__(self, processor):
        self.processor = processor

    def receive(self):
        return MockFileSatellites(
            self.processor.file_upload_registry_hub.link_file_upload_registry_file_log_file
        )


class MockFileSatellites:
    def __init__(self, linked_files):
        self.linked_files = linked_files

    def first(self):
        return MockFileSatellite(self.linked_files.first())

    def count(self):
        return self.linked_files.count()


class MockFileSatellite:
    def __init__(self, linked_file):
        self.linked_file = linked_file

    @property
    def log_file(self):
        excel_file = FileUploadFileStaticSatellite.objects.get(
            hub_entity=self.linked_file
        ).file
        return excel_file.name


class TestExcelLogFileMixin(TestCase, LogFileTestMixin):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.processor = MockDataProcessor()
        self.now_timestamp = timezone.now()
        self.processor.session_data = {"user_id": self.user.id}
        self.processor.file_upload_registry_hub.created_by = self.user
        self.processor.file_upload_registry_hub.created_at = self.now_timestamp

    def test_log_excel_file__no_registry(self):
        with self.assertRaises(AttributeError) as e:
            LogFileMixin().generate_log_file_excel("Fails")
        self.assertEqual(
            str(e.exception),
            "ExcelLogFileMixin has no file_upload_registry_hub attribute.",
        )

    def test_log_excel_file__no_session_data(self):
        with self.assertRaises(AttributeError) as e:
            MockNoSessionDataProcessor().generate_log_file_excel("Fails")
        self.assertEqual(
            str(e.exception),
            "ExcelLogFileMixin has no session_data attribute.",
        )

    def test_log_excel_file__generate_file(self):
        test_message = "Some message"
        self.processor.generate_log_file_excel(test_message)
        self.assert_log_excel_file(MockRegistryRepository(self.processor), test_message)
        self.assert_log_excel_file(
            MockRegistryRepository(self.processor), test_message[:4], _startswith=True
        )

    def test_log_excel_file__additional_data(self):
        test_message = "Test with additional data sheet"
        test_additional_data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        self.processor.generate_log_file_excel(
            test_message, additional_data=test_additional_data
        )
        self.assert_log_excel_file(
            MockRegistryRepository(self.processor),
            test_message,
            additional_data=test_additional_data,
        )

    def test_muktiple_log_files(self):
        test_message = "Some message"
        self.processor.generate_log_file_excel(test_message)
        test_message_2 = "Another message"
        self.processor.generate_log_file_excel(test_message_2)
        file_links = (
            self.processor.file_upload_registry_hub.link_file_upload_registry_file_log_file
        )
        # One file is linked
        self.assertEqual(
            file_links.count(),
            1,
        )
        log_file_hub = file_links.last()
        # Two files were generated
        file_sats = FileUploadFileStaticSatellite.objects.filter(
            hub_entity=log_file_hub
        )

        self.assertEqual(file_sats.all().count(), 2)

        excel_file = file_sats.first().file
        result_df = pd.read_excel(excel_file)
        self.assertEqual(
            result_df.set_index("Param").loc["Upload Message"].iloc[0], test_message
        )
        excel_file = file_sats.last().file
        result_df = pd.read_excel(excel_file)
        self.assertEqual(
            result_df.set_index("Param").loc["Upload Message"].iloc[0], test_message_2
        )
