from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.managers.file_upload_manager import FileUploadManager

class TestFileUploadManager(TestCase):
    def setUp(self):
        class MockFileUploadProcessor:
            def process(self, file):
                pass
        self.file_upload_processor = MockFileUploadProcessor()
        self.test_file_path = "/tmp/test_file.txt"
        with open(self.test_file_path, "w") as f:
            f.write("test")
        f.close()

    def test_fum_init(self):
        fum = FileUploadManager(
            file_upload_processor=self.file_upload_processor,
            file_path=self.test_file_path
        )
