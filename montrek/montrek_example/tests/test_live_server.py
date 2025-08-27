import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import LiveServerTestCase
from montrek_example.tests.factories.montrek_example_factories import SatD1Factory
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD


class TokenEndpointLiveTests(LiveServerTestCase):
    port = 8917

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = get_user_model()
        cls.password = TEST_USER_PASSWORD
        cls.user = user.objects.create_user(
            email="alice@example.com",
            password=cls.password,
        )
        cls.payload = {"email": cls.user.email, "password": cls.password}

    def test_obtain_token_via_http(self):
        # Test Data
        test_sat = SatD1Factory()
        # If your login uses email, change payload to {"email": self.user.email, "password": self.password}
        url = f"{self.live_server_url}/rest_api/token/"

        resp = requests.post(
            url, json=self.payload, headers={"Accept": "application/json"}, timeout=10
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

    def test_restricted_api_call__not_authorised(self):
        url = f"{self.live_server_url}/rest_api/token/"

        resp = requests.post(
            url, json=self.payload, headers={"Accept": "application/json"}, timeout=10
        )
        data = resp.json()
        token = data["access"]
        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/listrestricted?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(
            data["detail"], "You do not have permission to perform this action."
        )

    def _ensure_permission_exists_and_assign(self, codename="show_hubd"):
        # Grab any content type from the 'montrek_example' app
        ct = ContentType.objects.filter(app_label="montrek_example").first()
        self.assertIsNotNone(
            ct,
            "No ContentType found for app 'montrek_example'. "
            "Do you have at least one model in that app and are migrations applied?",
        )

        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={"name": "Can show hubd"},
        )
        self.user.user_permissions.add(perm)
        self.user.refresh_from_db()

    def test_restricted_api_call__authorised(self):
        test_sat = SatD1Factory()
        # Create + grant the permission required by the view
        self._ensure_permission_exists_and_assign("show_hubd")

        # Get a JWT
        token_url = f"{self.live_server_url}/rest_api/token/"
        resp = requests.post(
            token_url,
            json=self.payload,
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["access"]

        # Call the restricted endpoint with the Bearer token
        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/listrestricted?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        expected_data = {
            "field_d1_str": test_sat.field_d1_str,
            "field_d1_int": test_sat.field_d1_int,
            "value_date": None,
            "field_tsd2_float": None,
            "field_tsd2_int": None,
        }
        self.assertEqual(data, [expected_data])
