from django.test import TestCase
from baseclasses.managers.request_manager import RequestManager, RequestAuthenticator


class MockRequestManager(RequestManager):
    base_url = "https://httpbin.org/"
    authenticator = RequestAuthenticator(user="user", password="pass")


class MockRequestManagerNoAuth(RequestManager):
    base_url = "https://httpbin.org/"


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
        self.assertEqual(
            manager.message,
            "401 Client Error: UNAUTHORIZED for url: https://httpbin.org/basic-auth/user/pass",
        )
