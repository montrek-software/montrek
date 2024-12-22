from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.tests.mocks import (
    MockFileUploadProcessor,
    MockFileUploadProcessorFail,
    MockFileUploadProcessorPostCheckFail,
    MockFileUploadProcessorPreCheckFail,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class MockFileUploadManager(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessor
    do_process_file_async = False


class MockFileUploadManagerProcessorFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorFail
    do_process_file_async = False


class MockFileUploadManagerProcessorPreCheckFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorPreCheckFail
    do_process_file_async = False


class MockFileUploadManagerProcessorPostCheckFail(FileUploadManagerABC):
    file_upload_processor_class = MockFileUploadProcessorPostCheckFail
    do_process_file_async = False


class TestFileUploadManager(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "value_date": {
                        "filter_value": "2024-01-01",
                        "filter_negate": False,
                    }
                }
            },
        }
        self.session_data.update(filter_data)

    def test_fum_register_file_in_db(self):
        manager = MockFileUploadManager(
            session_data=self.session_data,
        )
        manager.register_file_in_db(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        fname_pattern = r"test_file.*\.txt"
        self.assertRegex(file_upload_registry.file, fname_pattern)
        self.assertEqual(file_upload_registry.file_name, "test_file.txt")
        self.assertEqual(file_upload_registry.file_type, "txt")
        self.assertEqual(file_upload_registry.upload_status, "pending")
        self.assertEqual(file_upload_registry.upload_message, "Upload is pending")

    def test_fum_upload_success(self):
        fum = MockFileUploadManager(
            session_data=self.session_data,
        )
        fum.upload_and_process(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "processed")
        self.assertEqual(file_upload_registry.upload_message, fum.processor.message)

    def test_fum_upload_failure(self):
        fum = MockFileUploadManagerProcessorFail(
            session_data=self.session_data,
        )
        fum.upload_and_process(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, fum.processor.message)

    def test_fum_pre_check_fails(self):
        fum = MockFileUploadManagerProcessorPreCheckFail(
            session_data=self.session_data,
        )
        fum.upload_and_process(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, fum.processor.message)

    def test_fum_post_check_fails(self):
        fum = MockFileUploadManagerProcessorPostCheckFail(
            session_data=self.session_data,
        )
        fum.upload_and_process(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, fum.processor.message)
