from django.urls import reverse
from rest_framework.test import APITestCase
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestRestAPITokens(APITestCase):
    def test_endpoints_not_redirected_to_user_login(self):
        for reverse_name in ("token_obtain_pair", "token_refresh", "token_verify"):
            with self.subTest(endpoint=reverse_name):
                url = reverse(reverse_name)
                resp = self.client.options(url)
                # Not redirected to /user/login/ via Response.url attribute
                self.assertNotEqual(getattr(resp, "url", None), "/user/login/")

                # Not redirected to /user/login/ via Location header
                self.assertFalse(
                    resp.has_header("Location")
                    and resp["Location"].startswith("/user/login/"),
                    msg=f"{reverse_name} unexpectedly redirected to login.",
                )

                # Not a redirect status
                self.assertNotIn(resp.status_code, (301, 302, 303, 307, 308))

    def test_no_valid_user_no_token(self):
        url = reverse("token_obtain_pair")
        payload = {"email": "unknown_user", "password": "password"}
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(
            resp.json()["detail"],
            "No active account found with the given credentials",
        )

    @add_logged_in_user
    def test_get_token_and_validate(self):
        url = reverse("token_obtain_pair")
        payload = {"email": self.user.email, "password": "S3cret!123"}
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

        access = resp.data["access"]
        refresh = resp.data["refresh"]

        # Verify access token
        verify_url = reverse("token_verify")
        v = self.client.post(verify_url, {"token": access}, format="json")
        self.assertEqual(v.status_code, 200, v.content)

        # Refresh to get a new access token
        refresh_url = reverse("token_refresh")
        r = self.client.post(refresh_url, {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("access", r.data)
