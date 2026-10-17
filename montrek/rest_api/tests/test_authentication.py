from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken

from baseclasses.views import REST_API_QUERY_PARAM
from rest_api.authentication import MontrekApiAuthentication
from user.tests.factories.montrek_user_factories import MontrekUserFactory

KEYCLOAK_TOKEN = "issued.by.keycloak"  # noqa: S105 - dummy test token  # nosec B105
OIDC_AUTHENTICATE = "mozilla_django_oidc.contrib.drf.OIDCAuthentication.authenticate"


def request_with_token(token: str | None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return APIRequestFactory().get("/", **headers)


class TestMontrekApiAuthentication(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.authentication = MontrekApiAuthentication()

    def test_no_token_is_no_authentication_attempt(self):
        self.assertIsNone(self.authentication.authenticate(request_with_token(None)))

    def test_montrek_token_authenticates(self):
        token = str(AccessToken.for_user(self.user))

        user, _ = self.authentication.authenticate(request_with_token(token))

        self.assertEqual(user, self.user)

    @override_settings(ENABLE_KEYCLOAK=False)
    def test_foreign_token_is_rejected_without_keycloak(self):
        with self.assertRaises(InvalidToken):
            self.authentication.authenticate(request_with_token(KEYCLOAK_TOKEN))

    @override_settings(ENABLE_KEYCLOAK=True)
    def test_foreign_token_is_checked_against_keycloak(self):
        with (
            patch(OIDC_AUTHENTICATE, return_value=(self.user, KEYCLOAK_TOKEN)),
            patch("mozilla_django_oidc.contrib.drf.get_oidc_backend"),
        ):
            user, token = self.authentication.authenticate(
                request_with_token(KEYCLOAK_TOKEN)
            )

        self.assertEqual(user, self.user)
        self.assertEqual(token, KEYCLOAK_TOKEN)

    @override_settings(ENABLE_KEYCLOAK=True)
    def test_montrek_token_does_not_reach_keycloak(self):
        token = str(AccessToken.for_user(self.user))

        with patch(OIDC_AUTHENTICATE) as oidc_authenticate:
            self.authentication.authenticate(request_with_token(token))

        oidc_authenticate.assert_not_called()


class TestRestApiViewWithKeycloakToken(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def get_uploads(self):
        return self.client.get(
            reverse("a1_view_uploads"),
            query_params={REST_API_QUERY_PARAM: "true"},
            headers={"Authorization": f"Bearer {KEYCLOAK_TOKEN}"},
        )

    @override_settings(ENABLE_KEYCLOAK=True)
    def test_keycloak_token_grants_access(self):
        with (
            patch(OIDC_AUTHENTICATE, return_value=(self.user, KEYCLOAK_TOKEN)),
            patch("mozilla_django_oidc.contrib.drf.get_oidc_backend"),
        ):
            response = self.get_uploads()

        self.assertEqual(response.status_code, 200, response.content)

    @override_settings(ENABLE_KEYCLOAK=False)
    def test_keycloak_token_is_unauthorized_without_keycloak(self):
        response = self.get_uploads()

        self.assertEqual(response.status_code, 401, response.content)
