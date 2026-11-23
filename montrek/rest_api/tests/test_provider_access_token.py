import time
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings
from django.urls import reverse
from jwt.algorithms import RSAAlgorithm
from rest_framework.exceptions import AuthenticationFailed

from baseclasses.views import REST_API_QUERY_PARAM
from rest_api.authentication import MontrekApiAuthentication
from rest_api.modules.provider_access_token import (
    ProviderAccessToken,
    ProviderTokenError,
)
from rest_api.tests.test_authentication import OIDC_AUTHENTICATE, request_with_token
from user.tests import oidc_mocks
from user.tests.factories.montrek_user_factories import MontrekUserFactory

AUDIENCE = "11111111-2222-3333-4444-555555555555"
SCOPE = "montrek.api"
KEY_ID = "key-1"
JWKS_URI = "https://login.example.com/tenant/keys"
PROVIDER_TOKEN_SETTINGS = {
    "ENABLE_OIDC": True,
    "OIDC_ISSUER_URL": oidc_mocks.ISSUER_URL,
    "OIDC_OP_JWKS_ENDPOINT": JWKS_URI,
    "OIDC_API_AUDIENCE": AUDIENCE,
    "OIDC_API_SCOPE": SCOPE,
}
PROVIDER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def published_keys() -> dict:
    jwk = RSAAlgorithm.to_jwk(PROVIDER_KEY.public_key(), as_dict=True)
    return {"keys": [{**jwk, "kid": KEY_ID, "use": "sig", "alg": "RS256"}]}


def provider_token(key=PROVIDER_KEY, algorithm="RS256", **claims) -> str:
    now = int(time.time())
    payload = {
        "iss": oidc_mocks.ISSUER_URL,
        "aud": AUDIENCE,
        "sub": "subject-1",
        "iat": now,
        "exp": now + 300,
        "scp": SCOPE,
        **claims,
    }
    payload = {name: value for name, value in payload.items() if value is not None}
    return jwt.encode(payload, key, algorithm=algorithm, headers={"kid": KEY_ID})


class ProviderTokenTestCase(TestCase):
    def setUp(self):
        ProviderAccessToken._jwks_clients.clear()
        self.addCleanup(ProviderAccessToken._jwks_clients.clear)
        fetch = mock.patch.object(
            jwt.PyJWKClient, "fetch_data", return_value=published_keys()
        )
        self.fetch_data = fetch.start()
        self.addCleanup(fetch.stop)


@override_settings(**PROVIDER_TOKEN_SETTINGS)
class TestProviderAccessToken(ProviderTokenTestCase):
    def assert_refused(self, token: str):
        with self.assertRaises(ProviderTokenError):
            ProviderAccessToken(token).claims()

    def test_a_token_for_montrek_with_the_scope_is_accepted(self):
        claims = ProviderAccessToken(provider_token()).claims()
        self.assertEqual(claims["sub"], "subject-1")

    def test_the_scope_may_come_as_scope_or_as_an_app_role(self):
        for claims in (
            {"scp": None, "scope": f"openid {SCOPE}"},
            {"scp": None, "roles": [SCOPE]},
        ):
            with self.subTest(claims=claims):
                ProviderAccessToken(provider_token(**claims)).claims()

    def test_a_token_for_another_audience_is_refused(self):
        # Such as a Microsoft Graph token another app obtained for the user.
        self.assert_refused(provider_token(aud="https://graph.microsoft.com"))

    def test_a_token_of_another_issuer_is_refused(self):
        self.assert_refused(provider_token(iss="https://login.example.com/other"))

    def test_an_expired_token_is_refused(self):
        now = int(time.time())
        self.assert_refused(provider_token(iat=now - 900, exp=now - 600))

    def test_a_token_signed_with_another_key_is_refused(self):
        self.assert_refused(provider_token(key=OTHER_KEY))

    def test_a_token_signed_with_a_shared_secret_is_refused(self):
        self.assert_refused(provider_token(key="a shared secret", algorithm="HS256"))

    def test_a_token_without_the_scope_is_refused(self):
        self.assert_refused(provider_token(scp="other.api", roles=["Other"]))

    def test_a_token_without_subject_or_expiry_is_refused(self):
        for claim in ("sub", "exp"):
            with self.subTest(claim=claim):
                self.assert_refused(provider_token(**{claim: None}))

    @override_settings(OIDC_API_SCOPE="")
    def test_without_a_scope_to_require_every_token_is_refused(self):
        self.assert_refused(provider_token())

    def test_the_keys_are_fetched_once(self):
        ProviderAccessToken(provider_token()).claims()
        ProviderAccessToken(provider_token()).claims()
        self.fetch_data.assert_called_once()


@override_settings(**PROVIDER_TOKEN_SETTINGS)
class TestApiAuthenticationWithProviderToken(ProviderTokenTestCase):
    def setUp(self):
        super().setUp()
        self.user = MontrekUserFactory(
            oidc_issuer=oidc_mocks.ISSUER_URL, oidc_subject="subject-1"
        )

    def authenticate(self, token: str):
        return MontrekApiAuthentication().authenticate(request_with_token(token))

    def test_the_linked_user_is_authenticated_without_asking_the_provider(self):
        token = provider_token()
        with mock.patch(OIDC_AUTHENTICATE) as userinfo:
            self.assertEqual(self.authenticate(token), (self.user, token))
        userinfo.assert_not_called()

    def test_an_application_authenticates_as_the_user_linked_to_it(self):
        application = MontrekUserFactory(
            oidc_issuer=oidc_mocks.ISSUER_URL, oidc_subject="service-principal"
        )
        token = provider_token(sub="service-principal", scp=None, roles=[SCOPE])
        self.assertEqual(self.authenticate(token)[0], application)

    def test_a_subject_no_user_is_linked_to_is_refused(self):
        with self.assertRaises(AuthenticationFailed):
            self.authenticate(provider_token(sub="unknown"))

    def test_the_same_subject_of_another_issuer_is_refused(self):
        self.user.oidc_issuer = "https://login.example.com/other"
        self.user.save()
        with self.assertRaises(AuthenticationFailed):
            self.authenticate(provider_token())

    def test_an_inactive_user_is_refused(self):
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(AuthenticationFailed):
            self.authenticate(provider_token())

    def test_an_invalid_token_is_refused(self):
        with self.assertRaises(AuthenticationFailed):
            self.authenticate(provider_token(aud="https://graph.microsoft.com"))

    def test_the_api_answers_401_for_an_invalid_token(self):
        response = self.client.get(
            reverse("a1_view_uploads"),
            query_params={REST_API_QUERY_PARAM: "true"},
            headers={"Authorization": f"Bearer {provider_token(scp='other.api')}"},
        )
        self.assertEqual(response.status_code, 401, response.content)

    def test_the_api_answers_for_a_valid_token(self):
        response = self.client.get(
            reverse("a1_view_uploads"),
            query_params={REST_API_QUERY_PARAM: "true"},
            headers={"Authorization": f"Bearer {provider_token()}"},
        )
        self.assertEqual(response.status_code, 200, response.content)

    @override_settings(OIDC_API_AUDIENCE="")
    def test_without_an_audience_the_userinfo_endpoint_decides(self):
        with (
            mock.patch(OIDC_AUTHENTICATE, return_value=(self.user, "t")) as userinfo,
            mock.patch("mozilla_django_oidc.contrib.drf.get_oidc_backend"),
        ):
            self.authenticate(provider_token())
        userinfo.assert_called_once()
        self.fetch_data.assert_not_called()
