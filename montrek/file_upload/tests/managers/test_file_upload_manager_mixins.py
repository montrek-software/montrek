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
from user.tests.factories.montrek_user_factories import MontrekUserFactory
import freezegun


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
    log_link_name = "link_file_upload_registry_log_file"

    def __init__(self):
        self.file_upload_registry_hub = FileUploadRegistryHubFactory.create()


class TestExcelLogFileMixin(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_log_excel_file__no_registry(self):
        with self.assertRaises(AttributeError) as e:
            LogFileMixin().generate_log_file_excel("Fails")
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

    def test_log_excel_file__generate_file(self):
        processor = MockDataProcessor()
        now_timestamp = timezone.now()
        processor.session_data = {"user_id": self.user.id}
        processor.file_upload_registry_hub.created_by = self.user
        processor.file_upload_registry_hub.created_at = now_timestamp
        test_message = "Some message"
        processor.generate_log_file_excel(test_message)
        file_links = (
            processor.file_upload_registry_hub.link_file_upload_registry_log_file
        )
        self.assertEqual(
            file_links.count(),
            1,
        )
        log_file_hub = file_links.first()
        excel_file = FileUploadFileStaticSatellite.objects.get(
            hub_entity=log_file_hub
        ).file
        self.assertTrue(excel_file)
        test_data_frame = pd.read_excel(excel_file)
        expected_df = pd.DataFrame(
            {
                "Upload Message": [test_message],
                "Upload Date": [now_timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                "Uploaded By": [self.user.email],
            },
            index=["Log Meta Data"],
        ).T.reset_index()
        expected_df = expected_df.rename(columns={"index": "Param"})
        pd.testing.assert_frame_equal(test_data_frame, expected_df, check_dtype=False)
