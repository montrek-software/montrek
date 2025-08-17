from django.urls import reverse
from rest_framework.test import APITestCase


class TokenObtainPairTests(APITestCase):
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
