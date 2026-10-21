import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import RequestFactory, TestCase
from django.urls import reverse
from info.repositories.download_registry_repositories import DownloadRegistryRepository
from reporting.tests.mocks import (
    MockMontrekReportFieldEditView,
    MockMontrekReportFieldEditViewValidationError,
    MockMontrekReportView,
    MockMontrekReportWithFormView,
)
from reporting.modules import mailed_downloads
from testing.decorators import add_logged_in_user
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestDownloadFileView(TestCase):
    @add_logged_in_user()
    def setUp(self):
        self.download_id = mailed_downloads.store(
            self.user.id, "test file.csv", ContentFile(b"a,b")
        )
        self.url = reverse(
            "download_reporting_file",
            kwargs={"download_id": self.download_id, "file_name": "test file.csv"},
        )
        self.path = mailed_downloads.storage_path(
            self.user.id, self.download_id, "test file.csv"
        )

    def test_download_once(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"a,b")
        self.assertEqual(
            response["Content-Disposition"], 'attachment; filename="test file.csv"'
        )
        self.assertFalse(default_storage.exists(self.path))
        self.assertEqual(DownloadRegistryRepository().receive().count(), 1)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_other_users_file_is_not_found(self):
        self.client.force_login(MontrekUserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(default_storage.exists(self.path))

    def test_unknown_download_is_not_found(self):
        url = reverse(
            "download_reporting_file",
            kwargs={"download_id": uuid.uuid4(), "file_name": "test file.csv"},
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_paths_are_not_accepted(self):
        other = default_storage.save("temp/other.csv", ContentFile(b"x"))
        self.addCleanup(default_storage.delete, other)
        for url in (
            "/reporting/download/temp/other.csv/",
            f"/reporting/download/{self.download_id}/../other.csv/",
            f"/reporting/download/{self.download_id}/../",
        ):
            with self.subTest(url):
                self.assertEqual(self.client.get(url).status_code, 404)
        self.assertTrue(default_storage.exists(other))


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
        # RequestFactory, unlike the test client, does not set this, so the
        # CSRF check of the report POST would reject the request.
        request._dont_enforce_csrf_checks = True

        response = MockMontrekReportWithFormView.as_view()(request)

        self.assertEqual(response.url, "/example/?field_1=ABC")

    def test_report_form_post_without_csrf_token_is_forbidden(self):
        request = self.factory.post("/example/", data={"field_1": "ABC"})
        request.user = self.user
        request.session = {}

        response = MockMontrekReportWithFormView.as_view()(request)

        self.assertEqual(response.status_code, 403)

    def test_report_form_renders_a_csrf_token(self):
        request = self.factory.get("/example/")
        request.user = self.user
        request.session = {}

        response = MockMontrekReportWithFormView.as_view()(request)

        self.assertIn("csrfmiddlewaretoken", response.context_data["report_form"])


class TestMontrekReportFieldEditView(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.factory = RequestFactory()
        self.field_edit_view = MockMontrekReportFieldEditView

    def test_get_edit_mode_renders_partial(self):
        """GET with mode=edit should render the edit field partial."""
        request = self.factory.get("/fake/url/?mode=edit&field=field_a")
        request.user = self.user
        request.session = {"method": "GET", "pk": 1}

        response = self.field_edit_view.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<div class="col-10">Test</div>', response.content)

    def test_get_non_edit_redirects(self):
        """GET without mode=edit should redirect."""
        request = self.factory.get("/fake/url/?mode=view&field=field_a")
        request.user = self.user
        request.session = {"method": "GET", "pk": 1}

        response = self.field_edit_view.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "")

    def test_post_cancel_renders_display_partial(self):
        """POST with action=cancel should render the display partial."""
        request = self.factory.post(
            "/fake/url/",
            {"action": "cancel", "field": "field_a"},
        )
        request.user = self.user
        request.session = {"method": "POST", "pk": 1}

        response = self.field_edit_view.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TestField", response.content)
        self.assertIn(b"field=field_a", response.content)

    def test_post_valid_form_calls_form_valid_and_creates(self):
        """POST valid field value should trigger form_valid and repository create."""
        request = self.factory.post(
            "/fake/url/",
            {"field": "field_a", "field_a": "new value"},
        )
        request.user = self.user
        request.session = {"method": "POST", "pk": 1}

        response = self.field_edit_view.as_view()(request)

        # Check that we got the display partial back
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"new value", response.content)

    def test_post_valid_form_calls_form_valid_and_creates__html(self):
        """POST valid field value should trigger form_valid and repository create."""
        request = self.factory.post(
            "/fake/url/",
            {"field": "field_a", "field_a": "new value\nschlummi"},
        )
        request.user = self.user
        request.session = {"method": "POST", "pk": 1}

        response = self.field_edit_view.as_view()(request)

        # Check that we got the escaped display partial back
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"new value<br>", response.content)

    def test_post_invalid_form_calls_form_invalid(self):
        """POST with invalid data should hit form_invalid branch."""
        request = self.factory.post(
            "/fake/url/",
            {"field": "field_a", "field_a": "bad input"},
        )
        request.user = self.user
        request.session = {"method": "POST", "pk": 1}

        response = MockMontrekReportFieldEditViewValidationError.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'<div class="error-message alert alert-danger">error: error</div>',
            response.content,
        )
