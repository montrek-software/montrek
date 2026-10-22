from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from user.modules.oidc_provider import OidcDiscoveryError, OidcProvider
from user.tests import oidc_mocks


@override_settings(OIDC_ISSUER_URL=oidc_mocks.ISSUER_URL)
class TestOidcProvider(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_endpoints_come_from_the_discovery_document(self):
        with mock.patch(
            oidc_mocks.REQUESTS_GET, return_value=oidc_mocks.discovery_response()
        ) as get:
            token_endpoint = OidcProvider.get_settings("OIDC_OP_TOKEN_ENDPOINT")
            jwks_endpoint = OidcProvider.get_settings("OIDC_OP_JWKS_ENDPOINT", None)

            self.assertEqual(
                str(token_endpoint), "https://login.example.com/tenant/token"
            )
            self.assertEqual(
                str(jwks_endpoint), "https://login.example.com/tenant/keys"
            )

        get.assert_called_once()
        self.assertEqual(get.call_args.args[0], oidc_mocks.DISCOVERY_URL)

    def test_endpoints_are_looked_up_only_when_used(self):
        with mock.patch(oidc_mocks.REQUESTS_GET) as get:
            OidcProvider.get_settings("OIDC_OP_AUTHORIZATION_ENDPOINT")
        get.assert_not_called()

    def test_explicit_endpoints_are_used_as_they_are(self):
        with (
            override_settings(
                OIDC_OP_TOKEN_ENDPOINT="https://keycloak/token"  # nosec B106: a URL
            ),
            mock.patch(oidc_mocks.REQUESTS_GET) as get,
        ):
            self.assertEqual(
                OidcProvider.get_settings("OIDC_OP_TOKEN_ENDPOINT"),
                "https://keycloak/token",
            )
        get.assert_not_called()

    @override_settings(OIDC_ISSUER_URL="")
    def test_without_issuer_url_nothing_is_discovered(self):
        with mock.patch(oidc_mocks.REQUESTS_GET) as get:
            self.assertIsNone(OidcProvider.get_settings("OIDC_OP_JWKS_ENDPOINT", None))
        get.assert_not_called()

    def test_other_settings_are_read_from_settings(self):
        with override_settings(OIDC_RP_CLIENT_ID="montrek"):
            self.assertEqual(OidcProvider.get_settings("OIDC_RP_CLIENT_ID"), "montrek")

    def test_document_of_another_issuer_is_refused(self):
        document = {**oidc_mocks.DISCOVERY_DOCUMENT, "issuer": "https://evil.example"}
        with (
            mock.patch(
                oidc_mocks.REQUESTS_GET,
                return_value=oidc_mocks.discovery_response(document),
            ),
            self.assertRaises(OidcDiscoveryError),
        ):
            str(OidcProvider.get_settings("OIDC_OP_TOKEN_ENDPOINT"))

    def test_unreachable_provider_raises_a_discovery_error(self):
        with (
            mock.patch(oidc_mocks.REQUESTS_GET, side_effect=oidc_mocks.unreachable()),
            self.assertRaises(OidcDiscoveryError),
            self.assertLogs("user.modules.oidc_provider", "ERROR"),
        ):
            str(OidcProvider.get_settings("OIDC_OP_TOKEN_ENDPOINT"))

    def test_document_that_is_no_json_object_raises_a_discovery_error(self):
        for document in (None, [], "issuer"):
            cache.clear()
            response = oidc_mocks.discovery_response()
            response.json.return_value = document
            with (
                self.subTest(document=document),
                mock.patch(oidc_mocks.REQUESTS_GET, return_value=response),
                self.assertRaises(OidcDiscoveryError),
                self.assertLogs("user.modules.oidc_provider", "ERROR"),
            ):
                str(OidcProvider.get_settings("OIDC_OP_TOKEN_ENDPOINT"))

    def test_missing_endpoint_raises_a_discovery_error(self):
        document = {**oidc_mocks.DISCOVERY_DOCUMENT}
        del document["userinfo_endpoint"]
        with (
            mock.patch(
                oidc_mocks.REQUESTS_GET,
                return_value=oidc_mocks.discovery_response(document),
            ),
            self.assertRaises(OidcDiscoveryError),
        ):
            str(OidcProvider.get_settings("OIDC_OP_USER_ENDPOINT"))

    def test_logout_url_is_the_end_session_endpoint(self):
        with mock.patch(
            oidc_mocks.REQUESTS_GET, return_value=oidc_mocks.discovery_response()
        ):
            self.assertEqual(
                OidcProvider.logout_url(), "https://login.example.com/tenant/logout"
            )

    def test_no_logout_url_without_end_session_endpoint_or_provider(self):
        document = {**oidc_mocks.DISCOVERY_DOCUMENT}
        del document["end_session_endpoint"]
        with mock.patch(
            oidc_mocks.REQUESTS_GET,
            return_value=oidc_mocks.discovery_response(document),
        ):
            self.assertIsNone(OidcProvider.logout_url())
        cache.clear()
        with (
            mock.patch(oidc_mocks.REQUESTS_GET, side_effect=oidc_mocks.unreachable()),
            self.assertLogs("user.modules.oidc_provider", "ERROR"),
        ):
            self.assertIsNone(OidcProvider.logout_url())

    @override_settings(OIDC_ISSUER_URL="", OIDC_OP_LOGOUT="https://keycloak/logout")
    def test_logout_url_of_the_keycloak_settings(self):
        self.assertEqual(OidcProvider.logout_url(), "https://keycloak/logout")
