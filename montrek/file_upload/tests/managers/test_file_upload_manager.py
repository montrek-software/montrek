from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.managers.file_upload_manager import FileUploadManager
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class MockFileUploadProcessor:
    message = "File processed"
    def process(self, file, registry):
        return True


class MockFileUploadProcessorFail:
    message = "File not processed"
    def process(self, file, registry):
        return False


class TestFileUploadManager(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )

    def test_fum_init(self):
        fum = FileUploadManager(
            file_upload_processor=MockFileUploadProcessor(), file=self.test_file
        )
        fum.init_upload()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        fname_pattern = r"uploads/test_file_.*\.txt"
        self.assertRegex(file_upload_registry.file, fname_pattern)
        self.assertEqual(file_upload_registry.file_name, "test_file.txt")
        self.assertEqual(file_upload_registry.file_type, "txt")
        self.assertEqual(file_upload_registry.upload_status, "pending")
        self.assertEqual(file_upload_registry.upload_message, "Upload is pending")


    def test_fum_upload_success(self):
        upload_processor = MockFileUploadProcessor()
        fum = FileUploadManager(
            file_upload_processor=upload_processor, file=self.test_file
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "processed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message )
        
    def test_fum_upload_failure(self):
        upload_processor = MockFileUploadProcessorFail()
        fum = FileUploadManager(
            file_upload_processor=upload_processor, file=self.test_file
        )
        fum.init_upload()
        fum.upload_and_process()
        file_upload_registry_query = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        self.assertEqual(file_upload_registry.upload_status, "failed")
        self.assertEqual(file_upload_registry.upload_message, upload_processor.message )
