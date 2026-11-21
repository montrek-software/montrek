import importlib
from unittest import mock

from django.apps import apps as django_apps

from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from mozilla_django_oidc.auth import OIDCAuthenticationBackend, default_username_algo
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


@override_settings(**OIDC_SETTINGS)
class TestUserFromTheProvider(TestCase):
    email = "new@example.com"

    def sign_in(self):
        with mock.patch.object(
            MontrekOIDCAuthenticationBackend,
            "get_userinfo",
            return_value={"email": self.email},
        ):
            return MontrekOIDCAuthenticationBackend().get_or_create_user(
                "access-token", "id-token", {}
            )

    def test_an_unknown_user_is_created(self):
        user = self.sign_in()

        self.assertEqual(user.email, self.email)
        self.assertTrue(get_user_model().objects.filter(email=self.email).exists())

    def test_a_created_user_has_no_password(self):
        user = self.sign_in()

        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password(default_username_algo(self.email)))

    @override_settings(OIDC_CREATE_USER=False)
    def test_without_user_creation_an_unknown_user_is_refused(self):
        self.assertIsNone(self.sign_in())
        self.assertFalse(get_user_model().objects.filter(email=self.email).exists())

    @override_settings(OIDC_CREATE_USER=False)
    def test_without_user_creation_a_known_user_signs_in(self):
        known = get_user_model().objects.create_user(email=self.email)

        self.assertEqual(self.sign_in(), known)


class TestMontrekUserManager(TestCase):
    def test_a_positional_argument_is_never_taken_as_the_password(self):
        with self.assertRaises(TypeError):
            get_user_model().objects.create_user("username", email="a@example.com")


class TestRemoveDerivedPasswords(TestCase):
    migration = importlib.import_module("user.migrations.0007_remove_derived_passwords")

    def test_only_derived_passwords_are_removed(self):
        user_model = get_user_model()
        derived = user_model.objects.create_user(
            email="oidc@example.com",
            password=default_username_algo("oidc@example.com"),
        )
        own = user_model.objects.create_user(
            email="own@example.com",
            password="a password of their own",  # nosec: B106: Testpasswort
        )
        without = user_model.objects.create_user(email="none@example.com")

        self.migration.remove_derived_passwords(django_apps, None)

        derived.refresh_from_db()
        own.refresh_from_db()
        without.refresh_from_db()
        self.assertFalse(derived.has_usable_password())
        self.assertTrue(own.check_password("a password of their own"))
        self.assertFalse(without.has_usable_password())

    def test_spells_the_library_algorithm(self):
        email = "Someone@Example.com"
        self.assertEqual(
            self.migration.derived_password(email), default_username_algo(email)
        )
