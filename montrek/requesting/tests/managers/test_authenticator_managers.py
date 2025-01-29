from django.test import TestCase
from requesting.managers.authenticator_managers import (
    RequestSlugAuthenticator,
    RequestUserPasswordAuthenticator,
    RequestBearerAuthenticator,
)


class TestRequestAuthenticators(TestCase):
    def test_user_password_authenticator(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "Basic dXNlcjpwYXNz")

    def test_bearer_authenticator(self):
        authenticator = RequestBearerAuthenticator({"token": "testtoken123"})
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "Bearer testtoken123")

    def test_slug_authenticator(self):
        authenticator = RequestSlugAuthenticator({"slug": "testslug", "token": "12456"})
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "testslug:12456")
