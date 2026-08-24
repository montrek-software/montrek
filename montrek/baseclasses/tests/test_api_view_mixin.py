"""CSRF handling of MontrekApiViewMixin.

APIView.as_view() marks the URL callable csrf_exempt so that token clients --
which carry no CSRF cookie -- can POST. Because that marker applies to every
method of the callable, the mixin has to hand the browser path back to
csrf_protect, otherwise mounting the mixin on a view with a form POST would
silently disable CSRF protection for that form.
"""

from baseclasses.views import (
    REST_API_QUERY_PARAM,
    MontrekApiViewMixin,
    MontrekRestApiView,
)
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path, reverse
from montrek.urls import urlpatterns as montrek_urlpatterns
from rest_framework import status
from rest_framework.response import Response
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD
from user.tests.factories.montrek_user_factories import MontrekUserFactory

REST_QUERY_PARAMS = {REST_API_QUERY_PARAM: "true"}


class ApiMixinTestView(MontrekApiViewMixin):
    def get(self, request, *args, **kwargs):
        # Hand out the CSRF cookie the browser POST test needs.
        get_token(request)
        return HttpResponse("get")

    def post(self, request, *args, **kwargs):
        if self._is_rest(request):
            return Response({"path": "rest"}, status=status.HTTP_200_OK)
        return HttpResponse("post")


# The project URLs are kept so that LOGIN_URL and the token endpoints resolve.
urlpatterns = [
    path("api-mixin-test/", ApiMixinTestView.as_view(), name="api_mixin_test"),
    *montrek_urlpatterns,
]


@override_settings(ROOT_URLCONF=__name__)
class TestMontrekApiViewMixinCsrf(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = MontrekUserFactory(password=TEST_USER_PASSWORD)
        self.url = reverse("api_mixin_test")

    def get_headers(self) -> dict[str, str]:
        payload = {"email": self.user.email, "password": TEST_USER_PASSWORD}
        response = self.client.post(reverse("token_obtain_pair"), payload)
        self.assertEqual(response.status_code, 200, response.content)
        return {"Authorization": f"Bearer {response.data['access']}"}

    def get_csrf_token(self) -> str:
        self.client.get(self.url)
        return self.client.cookies["csrftoken"].value

    def test_rest_post_without_csrf_token_is_accepted(self):
        response = self.client.post(
            self.url,
            query_params=REST_QUERY_PARAMS,
            headers=self.get_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"path": "rest"})

    def test_rest_post_without_token_is_unauthorized(self):
        response = self.client.post(self.url, query_params=REST_QUERY_PARAMS)
        self.assertEqual(response.status_code, 401, response.content)

    def test_browser_post_without_csrf_token_is_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403, response.content)

    def test_browser_post_with_csrf_token_is_accepted(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, data={"csrfmiddlewaretoken": self.get_csrf_token()}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content, b"post")

    def test_browser_get_is_accepted(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content, b"get")


class TestMontrekApiViewMixinAsView(TestCase):
    def test_as_view_keeps_django_and_drf_view_attributes(self):
        view = ApiMixinTestView.as_view()

        # RevokeFileUploadTask resolves a URL back to its view class through
        # view_class, and DRF's introspection uses cls/initkwargs.
        self.assertIs(view.view_class, ApiMixinTestView)
        self.assertIs(view.cls, ApiMixinTestView)
        self.assertEqual(view.initkwargs, {})
        self.assertTrue(view.csrf_exempt)

    def test_is_rest_request_follows_query_param(self):
        factory = RequestFactory()

        self.assertTrue(
            ApiMixinTestView.is_rest_request(factory.get("/", data=REST_QUERY_PARAMS))
        )
        self.assertFalse(ApiMixinTestView.is_rest_request(factory.get("/")))

    def test_rest_api_view_is_always_a_rest_request(self):
        self.assertTrue(MontrekRestApiView.is_rest_request(RequestFactory().get("/")))
