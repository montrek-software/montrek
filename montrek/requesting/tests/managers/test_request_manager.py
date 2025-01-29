from django.test import TestCase
from requesting.managers.request_manager import (
    RequestJsonManager,
)

from requesting.managers.authenticator_managers import (
    RequestUserPasswordAuthenticator,
    RequestBearerAuthenticator,
)


class MockRequestManager(RequestJsonManager):
    base_url = "https://httpbin.org/"
    request_kwargs = {"bla": "blubb"}


class TestRequestManager(TestCase):
    def test_get_json(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["user"], "user")

    def test_request_kwargs(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        request = manager.get_request("https://httpbin.org/basic-auth/user/pass", {})
        self.assertEqual(
            request.url, "https://httpbin.org/basic-auth/user/pass?bla=blubb"
        )

    def test_get_json_unauthorized(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "wrongpass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 401)
        self.assertEqual(response_json, {})
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass?bla=blubb",
        )

    def test_get_json_dummy(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("json")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertNotEqual(response_json, {})

    def test_get_json_no_valid_json(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "wrongpass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("html")
        self.assertEqual(manager.status_code, 0)
        self.assertEqual(manager.message, "No valid json returned")
        self.assertEqual(response_json, {})

    def test_bearer_authenticator(self):
        authenticator = RequestBearerAuthenticator({"token": "testtoken123"})
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("bearer")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["token"], "testtoken123")

    def test_wrong_authenticator(self):
        authenticator = RequestBearerAuthenticator({"token": "testtoken123"})
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.get_response("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 401)
        self.assertEqual(response_json, {})
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass?bla=blubb",
        )

    def test_post_json_dummy(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        manager = MockRequestManager(authenticator=authenticator)
        response_json = manager.post_response(
            "response-headers", {"freeform": "Hello Yello"}
        )
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertNotEqual(response_json, {})


class MockRequestNoConnectionManager(RequestJsonManager):
    base_url = "https://dummywummy.org/status/404"
    no_of_retries = 2
    sleep_time = 0.01


class TestRequestNoRequestManager(TestCase):
    def test_no_request_manager(self):
        authenticator = RequestUserPasswordAuthenticator(
            {"user": "user", "password": "pass"}
        )
        manager = MockRequestNoConnectionManager(authenticator=authenticator)
        manager.get_response("json")
        self.assertEqual(manager.status_code, 0)
        self.assertEqual(
            manager.message,
            "No request made after 2 attempts",
        )
