from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.urls import reverse
from reporting.views import download_reporting_file_view


class TestDownloadFileView(TestCase):
    def test_download_view_via_url(self):
        test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        temp_file_path = default_storage.save("temp/test_file.txt", test_file)
        test_url = reverse(
            "download_reporting_file", kwargs={"file_path": temp_file_path}
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 302)

    def test_download_view(self):
        test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        temp_file_path = default_storage.save("temp/test_file.txt", test_file)
        response = download_reporting_file_view(None, temp_file_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Content-Disposition"), "attachment; filename=test_file.txt"
        )

    def test_download_view_file_not_found(self):
        response = download_reporting_file_view(None, "Dummy.txt")
        self.assertEqual(response.status_code, 404)
