from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from file_upload.views import (
    MontrekUploadFileView,
    FileUploadRegistryView,
    MontrekDownloadFileView,
)
from baseclasses.pages import MontrekPage
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
    FileUploadFileStaticSatelliteFactory,
)
from testing.test_cases.view_test_cases import (
    MontrekListViewTestCase,
    MontrekFileResponseTestCase,
)


class MockPage(MontrekPage):
    def get_tabs(self):
        return []


class MockFileUploadView(MontrekUploadFileView):
    page_class = MockPage

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)

    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(self.request)


class TestMontrekUploadFileView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = MockFileUploadView("/fake-url/")

    def test_show_correct_url(self):
        test_file_upload_view = self.view
        response = test_file_upload_view.get(self.view.request)
        self.assertEqual(response.status_code, 200)


class TestFileUploadRegistryView(MontrekListViewTestCase):
    view_class = FileUploadRegistryView
    viewname = "montrek_upload_file"
    expected_no_of_rows = 3
    expected_columns = [
        "File Name",
        "Upload Status",
        "Upload Message",
        "Upload Date",
        "Uploaded By",
        "File",
    ]

    def build_factories(self):
        FileUploadRegistryStaticSatelliteFactory.create_batch(3)


class TestMontrekDownloadFileView(MontrekFileResponseTestCase):
    view_class = MontrekDownloadFileView
    viewname = "montrek_download_file"
    is_redirected = True

    def build_factories(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        upload_file = FileUploadFileStaticSatelliteFactory.create(file=self.test_file)
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            file_upload_file=upload_file.hub_entity
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.registrysat.hub_entity.pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")
