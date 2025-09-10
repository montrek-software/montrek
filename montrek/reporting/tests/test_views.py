import os

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from reporting.tests.mocks import MockMontrekReportView, MockMontrekReportWithFormView
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


class TestMontrekReportFormView(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user
        self.request.session = {}

    def test_get_no_report_form_as_default(self):
        response = MockMontrekReportView.as_view()(self.request)
        ctx = response.context_data
        self.assertEqual(ctx["report_form"], "")

    def test_get_report_form(self):
        response = MockMontrekReportWithFormView.as_view()(self.request)
        ctx = response.context_data
        self.assertNotEqual(ctx["report_form"], "")

    def test_report_view__get(self):
        request = self.factory.get("/?state=loading", HTTP_HX_REQUEST="true")
        request.user = self.user
        request.session = {}
        response = MockMontrekReportWithFormView.as_view()(request)
        self.assertIn("Init", str(response.content))

    def test_get_report_form__post(self):
        form_data = {"field_1": "ABC"}
        request = self.factory.post("/example/", data=form_data)
        request.user = self.user
        request.session = {}
        response = MockMontrekReportWithFormView.as_view()(request)
        self.assertEqual(response.url, "/example/?field_1=ABC")
