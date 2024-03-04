from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.managers.file_upload_manager import FileUploadManager
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class MockFileUploadProcessor:
    message = "File processed"

    def __init__(self, file_upload_registry_id, session_data, **kwargs):
        pass

    def pre_check(self, file_path):
        return True

    def process(self, file_path):
        return True

    def post_check(self, file_path):
        return True


class MockFileUploadProcessorFail(MockFileUploadProcessor):
    message = "File not processed"

    def process(self, file_path):
        return False


class MockFileUploadProcessorPreCheckFail(MockFileUploadProcessor):
    message = "Pre Check failed"

    def pre_check(self, file_path):
        return False


class MockFileUploadProcessorPostCheckFail(MockFileUploadProcessor):
    message = "Pre Check failed"

    def post_check(self, file_path):
        return False


class TestFileUploadManager(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_fum_init(self):
        upload_processor = MockFileUploadProcessor
        fum = FileUploadManager(
            file_upload_processor_class=upload_processor,
            file=self.test_file,
            session_data=self.session_data,
        )
        fum.init_upload()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        fname_pattern = r"test_file.*\.txt"
        self.assertRegex(file_upload_registry.file, fname_pattern)
        self.assertEqual(file_upload_registry.file_name, "test_file.txt")
        self.assertEqual(file_upload_registry.file_type, "txt")
        self.assertEqual(file_upload_registry.upload_status, "pending")
        self.assertEqual(file_upload_registry.upload_message, "Upload is pending")

    def test_fum_upload_success(self):
        upload_processor = MockFileUploadProcessor
        fum = FileUploadManager(
            file_upload_processor_class=upload_processor,
            file=self.test_file,
            session_data=self.session_data,
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "processed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message)

    def test_fum_upload_failure(self):
        upload_processor = MockFileUploadProcessorFail
        fum = FileUploadManager(
            file_upload_processor_class=upload_processor,
            file=self.test_file,
            session_data=self.session_data,
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message)

    def test_fum_pre_check_fails(self):
        upload_processor = MockFileUploadProcessorPreCheckFail
        fum = FileUploadManager(
            file_upload_processor_class=upload_processor,
            file=self.test_file,
            session_data=self.session_data,
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message)

    def test_fum_post_check_fails(self):
        upload_processor = MockFileUploadProcessorPostCheckFail
        fum = FileUploadManager(
            file_upload_processor_class=upload_processor,
            file=self.test_file,
            session_data=self.session_data,
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message)
