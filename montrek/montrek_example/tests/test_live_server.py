import uuid

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import LiveServerTestCase
from montrek_example.models.example_models import (  # adjust if your model name differs
    SatD1,
)
from montrek_example.tests.factories.montrek_example_factories import SatD1Factory
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD


class TokenEndpointLiveTests(LiveServerTestCase):
    port = 8917

    def setUp(self):
        user_model = get_user_model()
        # unique email each test, avoids any accidental collisions
        email = f"alice+{uuid.uuid4().hex[:8]}@example.com"
        self.password = TEST_USER_PASSWORD
        self.user = user_model.objects.create_user(email=email, password=self.password)
        self.payload = {"email": self.user.email, "password": self.password}

    # --- helpers -------------------------------------------------------------

    def _get_token(self):
        url = f"{self.live_server_url}/rest_api/token/"
        resp = requests.post(
            url, json=self.payload, headers={"Accept": "application/json"}, timeout=10
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()["access"]

    def _grant_perm(self, codename="show_hubd"):
        # Tie the custom permission to any model in your app; use a concrete model.
        ct = ContentType.objects.get_for_model(SatD1)
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={"name": "Can show hubd"},
        )
        self.user.user_permissions.add(perm)
        self.user.refresh_from_db()

    # --- tests ---------------------------------------------------------------

    def test_obtain_token_via_http(self):
        test_sat = SatD1Factory()

        token = self._get_token()

        # Optional verify endpoint
        verify_url = f"{self.live_server_url}/rest_api/api/token/verify/"
        v = requests.post(verify_url, json={"token": token}, timeout=10)
        self.assertEqual(v.status_code, 200, v.text)

        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/list?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)
        self.assertEqual(response.status_code, 200, response.text)

        data = response.json()
        expected = {
            "field_d1_str": test_sat.field_d1_str,
            "field_d1_int": test_sat.field_d1_int,
            "value_date": None,
            "field_tsd2_float": None,
            "field_tsd2_int": None,
        }
        self.assertEqual(data, [expected])

    def test_restricted_api_call__not_authorised(self):
        token = self._get_token()

        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/listrestricted?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(
            response.json()["detail"],
            "You do not have permission to perform this action.",
        )

    def test_restricted_api_call__authorised(self):
        test_sat = SatD1Factory()

        self._grant_perm("show_hubd")
        token = self._get_token()

        rest_api_url = (
            f"{self.live_server_url}/montrek_example/d/listrestricted?gen_rest_api=true"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(rest_api_url, headers=headers, timeout=10)
        self.assertEqual(response.status_code, 200, response.text)

        data = response.json()
        expected = {
            "field_d1_str": test_sat.field_d1_str,
            "field_d1_int": test_sat.field_d1_int,
            "value_date": None,
            "field_tsd2_float": None,
            "field_tsd2_int": None,
        }
        self.assertEqual(data, [expected])
