from django.test import TestCase
from baseclasses.managers.request_manager import RequestManager


class MockRequestManager(RequestManager):
    base_url = "https://httpbin.org/"


class TestRequestManager(TestCase):
    def test_get(self):
        manager = MockRequestManager()
        response = manager.get("basic-auth/user/pass")
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["authenticated"], True)
        self.assertEqual(response_json["user"], "user")
