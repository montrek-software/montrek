from typing import cast
from unittest.mock import MagicMock, patch

from baseclasses.pages import MontrekPage
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest, HttpResponse
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
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
from info.repositories.download_registry_repositories import DownloadRegistryRepository
from process_pipeline.dataclasses.registry_table_elements import (
    RegistryMessageTableElement,
)
from testing.decorators.add_logged_in_user import add_logged_in_user
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


def _get_response(_request: HttpRequest) -> HttpResponse:
    return HttpResponse()


class MockFileUploadView(MontrekUploadFileView):
    page_class = MockPage
    file_upload_manager_class = cast(type[FileUploadManagerABC], MockFileUploadManager)

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)

    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        self.request.user = AnonymousUser()
        session_middleware = SessionMiddleware(_get_response)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(_get_response)
        message_middleware.process_request(self.request)


class MockUploadableFileView(MontrekUploadFileView):
    """Concrete view for testing _check_file_type and POST / form_valid behavior."""

    page_class = MockPage
    accept = ".xlsx"

    def get_success_url(self):
        return "/success/"

    def configure_request(self, method="GET", file=None):
        if method == "POST":
            data = {"file": file} if file is not None else {}
            request = RequestFactory().post("/fake-url/", data=data)
        else:
            request = RequestFactory().get("/fake-url/")
        request.user = AnonymousUser()
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda r: None).process_request(request)
        self.request = request
        return request


class TestMontrekUploadFileView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = MockFileUploadView("/fake-url/")

    def test_show_correct_url(self):
        test_file_upload_view = self.view
        response = test_file_upload_view.get(self.view.request)
        self.assertEqual(response.status_code, 200)

    # --- get_file_type_error ---

    def test_get_file_type_error_reports_missing_file(self):
        view = MockUploadableFileView()
        view.configure_request()

        self.assertEqual(view.get_file_type_error(None), "No file attached")

    def test_get_file_type_error_reports_wrong_extension(self):
        view = MockUploadableFileView()
        view.configure_request()
        file = SimpleUploadedFile("data.csv", b"col1,col2")

        self.assertEqual(view.get_file_type_error(file), "File type CSV not allowed")

    def test_get_file_type_error_returns_none_on_correct_extension(self):
        view = MockUploadableFileView()
        view.configure_request()
        file = SimpleUploadedFile("report.xlsx", b"data")

        self.assertIsNone(view.get_file_type_error(file))

    def test_post_shows_file_type_message_and_renders_form(self):
        view = MockUploadableFileView()
        file = SimpleUploadedFile("data.csv", b"col1,col2")
        request = view.configure_request(method="POST", file=file)

        response = view.post(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "File type CSV not allowed",
            [str(m) for m in get_messages(request)],
        )

    # --- post ---

    def test_post_renders_form_when_form_has_no_file(self):
        view = MockUploadableFileView()
        request = view.configure_request(method="POST")

        response = view.post(request)

        self.assertEqual(response.status_code, 200)

    # --- form_valid ---

    def test_form_valid_adds_info_message_and_redirects_on_success(self):
        mock_instance = MagicMock()
        mock_instance.upload_and_process.return_value = True
        mock_instance.message = "3 records imported"

        view = MockUploadableFileView()
        view.file_upload_manager_class = MagicMock(return_value=mock_instance)
        file = SimpleUploadedFile("data.xlsx", b"data")
        request = view.configure_request(method="POST", file=file)

        response = view.post(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/success/")
        self.assertIn("3 records imported", [str(m) for m in get_messages(request)])

    def test_form_valid_adds_error_message_and_redirects_on_failure(self):
        mock_instance = MagicMock()
        mock_instance.upload_and_process.return_value = False
        mock_instance.message = "Upload failed"

        view = MockUploadableFileView()
        view.file_upload_manager_class = MagicMock(return_value=mock_instance)
        file = SimpleUploadedFile("data.xlsx", b"data")
        request = view.configure_request(method="POST", file=file)

        response = view.post(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn("Upload failed", [str(m) for m in get_messages(request)])


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


class TestFileUploadRegistryViewLiveRow(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            upload_status="in_progress", upload_message="Step 1 of 3"
        )
        self.url = reverse("montrek_upload_file")
        self.row_id = self.registrysat.get_hub_value_date().pk

    def _get_row(self, **params):
        return self.client.get(
            self.url, query_params={"live_row": self.row_id, **params}
        )

    def test_list_offers_live_rows(self):
        content = self.client.get(self.url).content.decode()
        self.assertIn(
            f'hx-get="{self.url}?live_row={self.row_id}&amp;live_shown=in_progress',
            content,
        )

    def test_active_row_keeps_polling(self):
        content = self._get_row().content.decode()
        self.assertTrue(content.lstrip().startswith("<tr"))
        self.assertNotIn("<html", content)
        self.assertIn("hx-get", content)
        self.assertIn("mt-live-label-active", content)
        self.assertIn("Step 1 of 3", content)

    def test_changes_since_last_shown_are_marked(self):
        content = self._get_row(
            live_shown="pending", live_shown_message="0"
        ).content.decode()
        self.assertIn("mt-live-label-changed", content)
        self.assertIn("mt-live-cell-changed", content)

    def test_unchanged_row_is_not_marked(self):
        content = self._get_row(
            live_shown="in_progress",
            live_shown_message=RegistryMessageTableElement.digest("Step 1 of 3"),
        ).content.decode()
        self.assertNotIn("mt-live-label-changed", content)
        self.assertNotIn("mt-live-cell-changed", content)

    def test_finished_row_stops_polling(self):
        self.registrysat.upload_status = "processed"
        self.registrysat.save()
        content = self._get_row().content.decode()
        self.assertNotIn("hx-get", content)
        self.assertNotIn("mt-live-label-active", content)

    def test_missing_row_stops_polling(self):
        response = self.client.get(self.url, query_params={"live_row": 0})
        self.assertEqual(response.status_code, 286)
        self.assertEqual(response.content, b"")

    def test_malformed_row_id_is_rejected(self):
        response = self.client.get(self.url, query_params={"live_row": "abc"})
        self.assertEqual(response.status_code, 400)

    def test_refresh_leaves_the_messages_alone(self):
        with patch.object(FileUploadRegistryView, "show_messages") as show_messages:
            self._get_row()
        show_messages.assert_not_called()


class TestMontrekDownloadFileView(MontrekFileResponseTestCase):
    view_class = MontrekDownloadFileView
    viewname = "montrek_download_file"
    is_redirected = True

    def build_factories(self):
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            generate_file_upload_file=True
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.registrysat.get_hub_value_date().pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)


class TestMontrekDownloadLogFileView(MontrekFileResponseTestCase):
    view_class = MontrekDownloadLogFileView
    viewname = "montrek_download_log_file"
    is_redirected = True

    def build_factories(self):
        self.registrysat = FileUploadRegistryStaticSatelliteFactory.create(
            generate_file_log_file=True
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.registrysat.get_hub_value_date().pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)
