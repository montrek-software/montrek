import os

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from reporting.tests.mocks import MockMontrekReportView
from reporting.views import download_reporting_file_view
from testing.decorators import add_logged_in_user


class TestDownloadFileView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

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
        request = self.factory.get("/")
        response = download_reporting_file_view(request, temp_file_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Content-Disposition"), "attachment; filename=test_file.txt"
        )
        self.assertFalse(os.path.exists(default_storage.path(temp_file_path)))
        test_url = reverse(
            "download_reporting_file", kwargs={"file_path": temp_file_path}
        )
        response = self.client.get(test_url)
        self.assertRaises(Http404)

    def test_download_view_file_not_found(self):
        request = self.factory.get("/")
        self.assertRaises(Http404, download_reporting_file_view, request, "Dummy.txt")


class TestMontrekReportView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @add_logged_in_user
    def test_get_view(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        response = MockMontrekReportView.as_view()(request)
        ctx = response.context_data
