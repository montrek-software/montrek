from django.test import TestCase
from requesting.managers.request_manager import (
    RequestJsonManager,
)

from requesting.managers.authenticator_managers import (
    RequestSlugAuthenticator,
    RequestUserPasswordAuthenticator,
    RequestBearerAuthenticator,
)


class MockRequestManager(RequestJsonManager):
    base_url = "https://httpbin.org/"
    authenticator_class = RequestUserPasswordAuthenticator
    authenticator_kwargs = {"user": "user", "password": "pass"}
    request_kwargs = {"bla": "blubb"}


class MockRequestManagerNoAuth(RequestJsonManager):
    base_url = "https://httpbin.org/"
    authenticator_class = RequestUserPasswordAuthenticator
    authenticator_kwargs = {"user": "user", "password": "wrongpass"}


class MockRequestManagerToken(RequestJsonManager):
    base_url = "https://httpbin.org/"
    authenticator_class = RequestBearerAuthenticator
    authenticator_kwargs = {"token": "testtoken123"}


class TestRequestManager(TestCase):
    def test_get_json(self):
        manager = MockRequestManager()
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["user"], "user")

    def test_request_kwargs(self):
        manager = MockRequestManager()
        request = manager.get_request("https://httpbin.org/basic-auth/user/pass", {})
        self.assertEqual(
            request.url, "https://httpbin.org/basic-auth/user/pass?bla=blubb"
        )

    def test_get_json_unauthorized(self):
        manager = MockRequestManagerNoAuth()
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 401)
        self.assertEqual(response_json, {})
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass",
        )

    def test_get_json_dummy(self):
        manager = MockRequestManager()
        response_json = manager.get_response("json")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertNotEqual(response_json, {})

    def test_get_json_no_valid_json(self):
        manager = MockRequestManagerNoAuth()
        response_json = manager.get_response("html")
        self.assertEqual(manager.status_code, 0)
        self.assertEqual(manager.message, "No valid json returned")
        self.assertEqual(response_json, {})

    def test_bearer_authenticator(self):
        manager = MockRequestManagerToken()
        response_json = manager.get_response("bearer")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["token"], "testtoken123")

    def test_wrong_authenticator(self):
        manager = MockRequestManagerToken()
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 401)
        self.assertEqual(response_json, {})
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass",
        )

    def test_post_json_dummy(self):
        manager = MockRequestManager()
        response_json = manager.post_response(
            "response-headers", {"freeform": "Hello Yello"}
        )
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertNotEqual(response_json, {})


class TestRequestAuthenticators(TestCase):
    def test_user_password_authenticator(self):
        authenticator = RequestUserPasswordAuthenticator(user="user", password="pass")
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "Basic dXNlcjpwYXNz")

    def test_bearer_authenticator(self):
        authenticator = RequestBearerAuthenticator(token="testtoken123")
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "Bearer testtoken123")

    def test_slug_authenticator(self):
        authenticator = RequestSlugAuthenticator(slug="testslug", token="12456")
        headers = authenticator.get_headers()
        self.assertEqual(headers["Authorization"], "testslug:12456")


class MockRequestNoConnectionManager(RequestJsonManager):
    base_url = "https://dummywummy.org/status/404"
    no_of_retries = 2
    sleep_time = 0.01


class TestRequestNoRequestManager(TestCase):
    def test_no_request_manager(self):
        manager = MockRequestNoConnectionManager()
        manager.get_response("json")
        self.assertEqual(manager.status_code, 0)
        self.assertEqual(
            manager.message,
            "No request made after 2 attempts",
        )
