from baseclasses.pages import MontrekPage
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.views import (
    FileUploadRegistryView,
    MontrekDownloadFileView,
    MontrekDownloadLogFileView,
    MontrekUploadFileView,
)
from testing.test_cases.view_test_cases import (
    MontrekFileResponseTestCase,
    MontrekListViewTestCase,
)


class MockPage(MontrekPage):
    def get_tabs(self):
        return []


class MockFileUploadProcessor:
    def process(self, file): ...

    def pre_check(self, file): ...

    def post_check(self, file): ...


class MockFileUploadManager(FileUploadRegistryRepositoryABC):
    file_upload_processor_class = MockFileUploadProcessor


class MockFileUploadView(MontrekUploadFileView):
    page_class = MockPage
    file_upload_manager_class = MockFileUploadManager

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)

    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        self.request.user = AnonymousUser()
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
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            generate_file_upload_file=True
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.registrysat.hub_entity.get_hub_value_date().pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")


class TestMontrekDownloadLogFileView(MontrekFileResponseTestCase):
    view_class = MontrekDownloadLogFileView
    viewname = "montrek_download_log_file"
    is_redirected = True

    def build_factories(self):
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            generate_file_log_file=True
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.registrysat.hub_entity.pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")
