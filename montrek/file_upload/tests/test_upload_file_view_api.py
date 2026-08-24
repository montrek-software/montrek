"""REST path of MontrekUploadFileView.

The API upload runs the same form, permission check and pipeline as the browser
upload; only authentication (JWT instead of a session) and the responses (JSON
instead of messages plus a redirect) differ. The pipeline itself is stubbed out
here -- montrek_example covers it end to end.
"""

from baseclasses.pages import MontrekPage
from django.conf import settings
from django.contrib.auth.models import Permission
from baseclasses.views import REST_API_QUERY_PARAM
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import path, reverse
from file_upload.views import MontrekUploadFileView
from montrek.urls import urlpatterns as montrek_urlpatterns
from process_pipeline.managers.montrek_pipeline_managers import TASK_SCHEDULED_MESSAGE
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD
from user.tests.factories.montrek_user_factories import MontrekUserFactory

REST_QUERY_PARAMS = {REST_API_QUERY_PARAM: "true"}
REGISTRY_ID = 42
ADD_USER_PERMISSION = "user.add_montrekuser"


class MockPage(MontrekPage):
    def get_tabs(self):
        return []


class StubRegistry:
    def __init__(self, upload_status: str):
        self.celery_task_id = "celery-task-id"
        self.upload_status = upload_status


class StubUploadManager:
    """Stands in for a FileUploadManagerABC without running the pipeline."""

    last_instance = None
    do_process_async = True
    registry_session_key = "file_upload_registry_id"
    status_field_name = "upload_status"
    upload_result = True

    def __init__(self, session_data):
        self.session_data = session_data
        self.message = TASK_SCHEDULED_MESSAGE
        self.uploaded_file = None
        self.pipeline_data = None
        StubUploadManager.last_instance = self

    def set_pipeline_data(self, pipeline_data):
        self.pipeline_data = pipeline_data

    def upload_and_process(self, file) -> bool:
        self.uploaded_file = file
        self.session_data[self.registry_session_key] = REGISTRY_ID
        return self.upload_result

    def get_registry(self) -> StubRegistry:
        return StubRegistry("pending" if self.do_process_async else "processed")


class StubFailingSyncUploadManager(StubUploadManager):
    do_process_async = False
    upload_result = False

    def __init__(self, session_data):
        super().__init__(session_data)
        self.message = "Upload failed"


class RestUploadTestView(MontrekUploadFileView):
    page_class = MockPage
    accept = ".csv"
    do_rest_upload = True
    file_upload_manager_class = StubUploadManager

    def get_success_url(self):
        return reverse("home")


class SyncRestUploadTestView(RestUploadTestView):
    file_upload_manager_class = StubFailingSyncUploadManager


class PermissionRestUploadTestView(RestUploadTestView):
    permission_required = [ADD_USER_PERMISSION]


class BrowserOnlyUploadTestView(RestUploadTestView):
    do_rest_upload = False


# The project URLs are kept so that LOGIN_URL and the token endpoints resolve.
urlpatterns = [
    path("rest-upload/", RestUploadTestView.as_view(), name="rest_upload"),
    path(
        "sync-rest-upload/", SyncRestUploadTestView.as_view(), name="sync_rest_upload"
    ),
    path(
        "permission-rest-upload/",
        PermissionRestUploadTestView.as_view(),
        name="permission_rest_upload",
    ),
    path(
        "browser-only-upload/",
        BrowserOnlyUploadTestView.as_view(),
        name="browser_only_upload",
    ),
    *montrek_urlpatterns,
]


@override_settings(ROOT_URLCONF=__name__)
class TestMontrekUploadFileViewApi(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory(password=TEST_USER_PASSWORD)
        self.url = reverse("rest_upload")
        StubUploadManager.last_instance = None

    def get_headers(self) -> dict[str, str]:
        payload = {"email": self.user.email, "password": TEST_USER_PASSWORD}
        response = self.client.post(reverse("token_obtain_pair"), payload)
        self.assertEqual(response.status_code, 200, response.content)
        return {"Authorization": f"Bearer {response.data['access']}"}

    def post_file(self, url=None, file=None, headers=None, **kwargs):
        data = {} if file is None else {"file": file}
        return self.client.post(
            url or self.url,
            data=data,
            query_params=REST_QUERY_PARAMS,
            headers=self.get_headers() if headers is None else headers,
            **kwargs,
        )

    @staticmethod
    def csv_file(name="data.csv") -> SimpleUploadedFile:
        return SimpleUploadedFile(name, b"col1,col2\n1,2", content_type="text/csv")

    def test_upload_without_token_is_unauthorized(self):
        response = self.post_file(file=self.csv_file(), headers={})

        self.assertEqual(response.status_code, 401, response.content)

    def test_upload_with_token_is_accepted(self):
        response = self.post_file(file=self.csv_file())

        self.assertEqual(response.status_code, 202, response.content)
        self.assertEqual(
            response.json(),
            {
                "registry_id": REGISTRY_ID,
                "celery_task_id": "celery-task-id",
                "status": "pending",
                "message": TASK_SCHEDULED_MESSAGE,
            },
        )

    def test_upload_hands_the_file_and_the_user_to_the_manager(self):
        self.post_file(file=self.csv_file())

        manager = StubUploadManager.last_instance
        self.assertEqual(manager.uploaded_file.name, "data.csv")
        # The pipeline mails the uploader, so the JWT user has to reach it.
        self.assertEqual(manager.session_data["user_id"], self.user.id)

    def test_upload_of_wrong_file_type_is_unsupported_media_type(self):
        response = self.post_file(file=self.csv_file(name="data.xlsx"))

        self.assertEqual(response.status_code, 415, response.content)
        self.assertEqual(response.json(), {"detail": "File type XLSX not allowed"})

    def test_upload_without_file_is_bad_request(self):
        response = self.post_file()

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("file", response.json()["errors"])

    def test_failed_synchronous_upload_is_unprocessable(self):
        response = self.post_file(url=reverse("sync_rest_upload"), file=self.csv_file())

        self.assertEqual(response.status_code, 422, response.content)
        self.assertEqual(response.json()["message"], "Upload failed")

    def test_upload_without_the_required_permission_is_forbidden(self):
        response = self.post_file(
            url=reverse("permission_rest_upload"), file=self.csv_file()
        )

        self.assertEqual(response.status_code, 403, response.content)

    def test_upload_with_the_required_permission_is_accepted(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_montrekuser")
        )

        response = self.post_file(
            url=reverse("permission_rest_upload"), file=self.csv_file()
        )

        self.assertEqual(response.status_code, 202, response.content)

    def test_view_without_rest_upload_opt_in_stays_browser_only(self):
        response = self.post_file(
            url=reverse("browser_only_upload"), file=self.csv_file()
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(str(settings.LOGIN_URL)))


@override_settings(ROOT_URLCONF=__name__)
class TestMontrekUploadFileViewBrowserPath(TestCase):
    """The browser upload keeps working the way the login_required decorator,
    which the REST path replaced, made it work."""

    def setUp(self):
        self.user = MontrekUserFactory(password=TEST_USER_PASSWORD)
        self.url = reverse("rest_upload")

    def test_anonymous_request_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(str(settings.LOGIN_URL)))

    def test_logged_in_request_renders_the_upload_form(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "upload_form.html")

    def test_logged_in_upload_redirects_to_the_success_url(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            data={
                "file": SimpleUploadedFile(
                    "data.csv", b"col1,col2\n1,2", content_type="text/csv"
                )
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("home"))
