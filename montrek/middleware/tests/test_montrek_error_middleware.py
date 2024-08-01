from django.contrib.messages.test import MessagesTestMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from baseclasses.errors.montrek_user_error import MontrekError
from middleware import MontrekErrorMiddleware
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


class MontrekErrorMiddlewareTest(MessagesTestMixin, TestCase):
    def setUp(self):
        self.middleware = MontrekErrorMiddleware(get_response=MockView.as_view())
        self.request = RequestFactory().get("/test/")
        SessionMiddleware(lambda request: None).process_request(self.request)
        MessageMiddleware(lambda request: None).process_request(self.request)

    def test_process_exception__montrek_error(self):
        self.request.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword"
        )
        exception = MontrekError("test")
        response = self.middleware.process_exception(self.request, exception)
        messages = _get_messages_from_storage(self.request)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "test",
        )
        self.assertEqual(messages[0].level, ERROR)

        self.request.META["HTTP_REFERER"] = "previous"
        response = self.middleware.process_exception(self.request, exception)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "previous")
