from unittest import mock

from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from user.backends import MontrekOIDCAuthenticationBackend
from user.tests import oidc_mocks

OIDC_SETTINGS = {
    "OIDC_ISSUER_URL": oidc_mocks.ISSUER_URL,
    "OIDC_RP_CLIENT_ID": "montrek",
    "OIDC_RP_CLIENT_SECRET": "",
    "OIDC_RP_SIGN_ALGO": "RS256",
}


@override_settings(**OIDC_SETTINGS)
class TestMontrekOIDCAuthenticationBackend(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_is_created_without_reaching_the_provider(self):
        with mock.patch(oidc_mocks.REQUESTS_GET) as get:
            MontrekOIDCAuthenticationBackend()
        get.assert_not_called()

    def test_uses_the_discovered_endpoints(self):
        with mock.patch(
            oidc_mocks.REQUESTS_GET, return_value=oidc_mocks.discovery_response()
        ):
            backend = MontrekOIDCAuthenticationBackend()
            self.assertEqual(
                str(backend.OIDC_OP_USER_ENDPOINT), "https://login.example.com/userinfo"
            )

    def test_accepts_tokens_of_the_configured_issuer(self):
        payload = {"iss": oidc_mocks.ISSUER_URL, "email": "a@b.de"}
        with mock.patch.object(
            OIDCAuthenticationBackend, "verify_token", return_value=payload
        ):
            self.assertEqual(
                MontrekOIDCAuthenticationBackend().verify_token("token"), payload
            )

    def test_refuses_tokens_of_another_issuer(self):
        payload = {"iss": "https://evil.example", "email": "a@b.de"}
        with (
            mock.patch.object(
                OIDCAuthenticationBackend, "verify_token", return_value=payload
            ),
            self.assertRaises(SuspiciousOperation),
        ):
            MontrekOIDCAuthenticationBackend().verify_token("token")

    @override_settings(
        OIDC_ISSUER_URL="",
        OIDC_OP_TOKEN_ENDPOINT="https://kc/token",  # nosec B106: a URL
    )
    def test_without_issuer_url_the_issuer_is_not_checked(self):
        payload = {"iss": "https://auth-default.127.0.0.1/realms/r"}
        with (
            override_settings(
                OIDC_OP_USER_ENDPOINT="https://kc/userinfo",
                OIDC_OP_JWKS_ENDPOINT="https://kc/certs",
            ),
            mock.patch.object(
                OIDCAuthenticationBackend, "verify_token", return_value=payload
            ),
        ):
            self.assertEqual(
                MontrekOIDCAuthenticationBackend().verify_token("token"), payload
            )
