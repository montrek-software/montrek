"""How the redirecting middlewares answer an htmx request.

An XHR follows a 302 by itself, so htmx never sees the redirect - it gets the
target page with status 200 and swaps it into the triggering element's
``hx-target``, which defaults to the element itself. Clicking the close action
on the risk report without the permission therefore rendered a whole page inside
the button, and the message explaining the denial went in there with it.

``HX-Redirect`` is the answer instead, and it is the one
``MontrekPostActionView.action_response`` already gave on its success path -
only the failure paths disagreed.
"""

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View

from baseclasses.errors.montrek_user_error import MontrekError
from middleware import (
    LoginRequiredMiddleware,
    MontrekErrorMiddleware,
    PermissionErrorMiddleware,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory

HTMX_HEADERS = {"HTTP_HX_REQUEST": "true"}


class MockView(View):
    def get(self, request):
        return HttpResponse()


class HtmxRedirectTestCase(TestCase):
    def build_request(self, htmx: bool):
        request = RequestFactory().get("/test/", **(HTMX_HEADERS if htmx else {}))
        SessionMiddleware(lambda _: None).process_request(request)
        MessageMiddleware(lambda _: None).process_request(request)
        # The factory, not a fixed address: one test builds two requests and
        # the email is unique.
        request.user = MontrekUserFactory()
        return request

    def assert_navigates(self, response):
        """204 + HX-Redirect: htmx navigates instead of swapping a body in."""
        self.assertEqual(response.status_code, 204)
        self.assertTrue(response["HX-Redirect"])
        self.assertFalse(response.content)

    def assert_plain_redirect(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("HX-Redirect", response)


class TestPermissionDenied(HtmxRedirectTestCase):
    def _respond(self, htmx: bool):
        request = self.build_request(htmx)
        return PermissionErrorMiddleware(get_response=MockView.as_view()), request

    def test_an_htmx_request_is_told_to_navigate(self):
        """The reported bug: the denial used to be swapped into the button."""
        middleware, request = self._respond(htmx=True)

        response = middleware.process_exception(request, PermissionDenied())

        self.assert_navigates(response)

    def test_an_ordinary_request_still_gets_a_redirect(self):
        middleware, request = self._respond(htmx=False)

        response = middleware.process_exception(request, PermissionDenied())

        self.assert_plain_redirect(response)

    def test_an_anonymous_htmx_request_is_sent_to_the_login_page(self):
        request = self.build_request(htmx=True)
        request.user = AnonymousUser()
        middleware = PermissionErrorMiddleware(get_response=MockView.as_view())

        response = middleware.process_exception(request, PermissionDenied())

        self.assert_navigates(response)
        self.assertEqual(response["HX-Redirect"], settings.LOGIN_URL)


class TestMontrekError(HtmxRedirectTestCase):
    def _respond(self, htmx: bool):
        request = self.build_request(htmx)
        middleware = MontrekErrorMiddleware(get_response=MockView.as_view())
        return middleware.process_exception(request, MontrekError("nope"))

    def test_an_htmx_request_is_told_to_navigate(self):
        self.assert_navigates(self._respond(htmx=True))

    def test_an_ordinary_request_still_gets_a_redirect(self):
        self.assert_plain_redirect(self._respond(htmx=False))


class TestLoginRequired(HtmxRedirectTestCase):
    """A session that expires while a page is open is usually noticed by an
    htmx call, which would otherwise swap the login page into whatever was
    clicked."""

    def _respond(self, htmx: bool):
        request = self.build_request(htmx)
        request.user = AnonymousUser()
        return LoginRequiredMiddleware(get_response=MockView.as_view())(request)

    def test_an_htmx_request_is_told_to_navigate(self):
        response = self._respond(htmx=True)

        self.assert_navigates(response)
        self.assertEqual(response["HX-Redirect"], settings.LOGIN_URL)

    def test_an_ordinary_request_still_gets_a_redirect(self):
        self.assert_plain_redirect(self._respond(htmx=False))

    def test_each_request_gets_its_own_response(self):
        """The redirect used to be one instance built in __init__ and handed to
        every unauthenticated request."""
        self.assertIsNot(self._respond(htmx=False), self._respond(htmx=False))
