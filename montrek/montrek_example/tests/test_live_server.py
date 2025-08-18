import requests
from django.contrib.auth import get_user_model
from django.test import LiveServerTestCase
from montrek_example.tests.factories.montrek_example_factories import SatD1Factory
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD


class TokenEndpointLiveTests(LiveServerTestCase):
    port = 8917

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.password = TEST_USER_PASSWORD
        cls.user = User.objects.create_user(
            email="alice@example.com",
            password=cls.password,
        )

    def test_obtain_token_via_http(self):
        # Test Data
        test_sat = SatD1Factory()
        # If your login uses email, change payload to {"email": self.user.email, "password": self.password}
        payload = {"email": self.user.email, "password": self.password}
        url = f"{self.live_server_url}/rest_api/token/"

        resp = requests.post(
            url, json=payload, headers={"Accept": "application/json"}, timeout=10
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        token = data["access"]

        # Optional: verify token if you expose /verify/
        verify_url = f"{self.live_server_url}/rest_api/api/token/verify/"
        v = requests.post(verify_url, json={"token": token}, timeout=10)
        self.assertEqual(v.status_code, 200, v.text)

        # Call Rest Api call
        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/list?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)
        data = response.json()
        expected_data = {
            "field_d1_str": test_sat.field_d1_str,
            "field_d1_int": test_sat.field_d1_int,
            "value_date": None,
            "field_tsd2_float": None,
            "field_tsd2_int": None,
        }
        self.assertEqual(data, [expected_data])
