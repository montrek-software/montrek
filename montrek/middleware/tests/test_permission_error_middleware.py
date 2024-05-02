from django.contrib.messages.test import MessagesTestMixin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from middleware import PermissionErrorMiddleware
from django.views import View
from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages import get_messages
from django.contrib.messages import ERROR


class MockView(View):
    def get(self, request):
        return HttpResponse()


def _get_messages_from_storage(request):
    return [m for m in get_messages(request)]


class PermissionErrorMiddlewareTestCase(MessagesTestMixin, TestCase):
    def setUp(self):
        self.middleware = PermissionErrorMiddleware(get_response=MockView.as_view())
        self.request = RequestFactory().get("/test/")
        SessionMiddleware(lambda request: None).process_request(self.request)
        MessageMiddleware(lambda request: None).process_request(self.request)

    def test_process_exception_permission_denied_authenticated_user(self):
        self.request.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword"
        )
        exception = PermissionDenied()
        response = self.middleware.process_exception(self.request, exception)
        messages = _get_messages_from_storage(self.request)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "You do not have the required permissions to access this page.",
        )
        self.assertEqual(messages[0].level, ERROR)

        self.request.META["HTTP_REFERER"] = "previous"
        response = self.middleware.process_exception(self.request, exception)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "previous")

    def test_process_exception_permission_denied_anonymous_user(self):
        self.request.user = AnonymousUser()
        exception = PermissionDenied()
        response = self.middleware.process_exception(self.request, exception)
        messages = _get_messages_from_storage(self.request)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, reverse("login"))
        self.assertEqual(
            str(messages[0]),
            "You do not have the required permissions to access this page.",
        )
        self.assertEqual(messages[0].level, ERROR)
