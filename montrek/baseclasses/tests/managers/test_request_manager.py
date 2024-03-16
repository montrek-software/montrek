from django.test import TestCase
from baseclasses.managers.request_manager import (
    RequestManager,
    RequestUserPasswordAuthenticator,
    RequestBearerAuthenticator,
)


class MockRequestManager(RequestManager):
    base_url = "https://httpbin.org/"
    authenticator = RequestUserPasswordAuthenticator(user="user", password="pass")


class MockRequestManagerNoAuth(RequestManager):
    base_url = "https://httpbin.org/"
    authenticator = RequestUserPasswordAuthenticator(user="user", password="wrongpass")


class MockRequestManagerToken(RequestManager):
    base_url = "https://httpbin.org/"
    authenticator = RequestBearerAuthenticator(token="testtoken123")


class TestRequestManager(TestCase):
    def test_get_json(self):
        manager = MockRequestManager()
        response_json = manager.get_json("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["user"], "user")

    def test_get_json_unauthorized(self):
        manager = MockRequestManagerNoAuth()
        response_json = manager.get_json("basic-auth/user/pass")
        self.assertEqual(manager.status_code, 401)
        self.assertEqual(response_json, {})
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass",
        )

    def test_get_json_dummy(self):
        manager = MockRequestManager()
        response_json = manager.get_json("json")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertNotEqual(response_json, {})

    def test_get_json_no_valid_json(self):
        manager = MockRequestManagerNoAuth()
        response_json = manager.get_json("html")
        self.assertEqual(manager.status_code, 0)
        self.assertEqual(manager.message, "No valid json returned")
        self.assertEqual(response_json, {})

    def test_bearer_authenticator(self):
        manager = MockRequestManagerToken()
        response_json = manager.get_json("bearer")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.message, "OK")
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["token"], "testtoken123")
