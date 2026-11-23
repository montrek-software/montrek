import importlib
from unittest import mock

from django.apps import apps as django_apps

from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from mozilla_django_oidc.auth import OIDCAuthenticationBackend, default_username_algo
from user.backends import MontrekOIDCAuthenticationBackend
from user.repositories.user_repository import MontrekUserRepository
from user.tests import oidc_mocks
from user.tests.factories.group_factories import GroupFactory

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
    subject = "subject-1"

    def sign_in(self, email=None, subject=None, id_token_subject=None):
        subject = subject or self.subject
        claims = {"sub": subject, "email": email or self.email}
        payload = {"sub": id_token_subject or subject}
        with mock.patch.object(
            OIDCAuthenticationBackend, "get_userinfo", return_value=claims
        ):
            return MontrekOIDCAuthenticationBackend().get_or_create_user(
                "access-token", "id-token", payload
            )

    def user(self, email=None, issuer="", subject=""):
        return get_user_model().objects.create_user(
            email=email or self.email, oidc_issuer=issuer, oidc_subject=subject
        )

    def test_an_unknown_user_is_created_and_linked(self):
        user = self.sign_in()

        self.assertEqual(user.email, self.email)
        self.assertEqual(
            (user.oidc_issuer, user.oidc_subject), (oidc_mocks.ISSUER_URL, self.subject)
        )

    def test_a_created_user_has_no_password(self):
        user = self.sign_in()

        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password(default_username_algo(self.email)))

    @override_settings(OIDC_CREATE_USER=False)
    def test_without_user_creation_an_unknown_user_is_refused(self):
        self.assertIsNone(self.sign_in())
        self.assertFalse(get_user_model().objects.filter(email=self.email).exists())

    @override_settings(OIDC_CREATE_USER=False)
    def test_a_known_user_is_linked_by_email_at_the_first_sign_in(self):
        known = self.user()

        self.assertEqual(self.sign_in(), known)
        known.refresh_from_db()
        self.assertEqual(
            (known.oidc_issuer, known.oidc_subject),
            (oidc_mocks.ISSUER_URL, self.subject),
        )

    def test_a_linked_user_is_found_by_subject_after_an_email_change(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)

        self.assertEqual(self.sign_in(email="renamed@example.com"), known)
        known.refresh_from_db()
        self.assertEqual(known.email, "renamed@example.com")

    def test_an_email_another_user_has_is_not_taken_over(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)
        self.user(email="other@example.com")

        with self.assertLogs("user.backends", "WARNING"):
            self.assertEqual(self.sign_in(email="Other@example.com"), known)
        known.refresh_from_db()
        self.assertEqual(known.email, self.email)

    @override_settings(ADMIN_EMAIL="new@example.com")
    def test_the_provisioned_admin_keeps_admin_email(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)

        with self.assertLogs("user.backends", "WARNING"):
            self.sign_in(email="renamed@example.com")
        known.refresh_from_db()
        self.assertEqual(known.email, self.email)

    def test_an_email_two_users_have_in_different_case_is_refused(self):
        self.user(email="Person@example.com")
        self.user(email="person@example.com", issuer=oidc_mocks.ISSUER_URL, subject="2")

        with self.assertRaises(SuspiciousOperation):
            self.sign_in(email="person@example.com")

    def test_a_link_made_meanwhile_by_another_subject_is_kept(self):
        known = self.user()
        backend = MontrekOIDCAuthenticationBackend()
        stale = get_user_model().objects.get(pk=known.pk)
        backend.update_user(known, {"sub": "subject-2", "email": self.email})

        with self.assertRaises(SuspiciousOperation):
            backend.update_user(stale, {"sub": self.subject, "email": self.email})
        known.refresh_from_db()
        self.assertEqual(known.oidc_subject, "subject-2")

    def test_a_concurrent_change_to_the_same_email_keeps_the_old_one(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)
        with mock.patch.object(
            get_user_model(), "save", side_effect=IntegrityError("duplicate")
        ):
            changed = MontrekUserRepository().change_email(known, "taken@example.com")
        self.assertFalse(changed)
        self.assertEqual(known.email, self.email)

    def test_a_change_of_case_only_keeps_the_email(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)

        self.sign_in(email="New@Example.com")
        known.refresh_from_db()
        self.assertEqual(known.email, self.email)

    def test_another_subject_with_the_email_of_a_linked_user_is_refused(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject="subject-2")

        for create_user in (True, False):
            with (
                self.subTest(create_user=create_user),
                override_settings(OIDC_CREATE_USER=create_user),
            ):
                try:
                    user = self.sign_in()
                except SuspiciousOperation:
                    user = None
                self.assertIsNone(user)
                known.refresh_from_db()
                self.assertEqual(known.oidc_subject, "subject-2")
                self.assertEqual(get_user_model().objects.count(), 1)

    def test_a_user_linked_at_another_issuer_is_linked_again_by_email(self):
        # After a switch of provider, e.g. from Keycloak to Entra ID.
        known = self.user(issuer="https://old.example.com/realms/r", subject="old")

        self.assertEqual(self.sign_in(), known)
        known.refresh_from_db()
        self.assertEqual(
            (known.oidc_issuer, known.oidc_subject),
            (oidc_mocks.ISSUER_URL, self.subject),
        )

    def test_userinfo_of_another_subject_than_the_id_token_is_refused(self):
        response = mock.Mock()
        response.json.return_value = {"sub": "subject-2", "email": self.email}
        with (
            override_settings(OIDC_OP_USER_ENDPOINT="https://login.example.com/u"),
            mock.patch("mozilla_django_oidc.auth.requests.get", return_value=response),
            self.assertRaises(SuspiciousOperation),
        ):
            MontrekOIDCAuthenticationBackend().get_userinfo(
                "access-token", "id-token", {"sub": self.subject}
            )

    def test_claims_without_a_subject_are_refused(self):
        backend = MontrekOIDCAuthenticationBackend()
        self.assertFalse(backend.verify_claims({"email": self.email}))
        self.assertTrue(
            backend.verify_claims({"sub": self.subject, "email": self.email})
        )

    def test_a_rest_api_token_without_id_token_signs_in(self):
        known = self.user(issuer=oidc_mocks.ISSUER_URL, subject=self.subject)
        with mock.patch.object(
            OIDCAuthenticationBackend,
            "get_userinfo",
            return_value={"sub": self.subject, "email": self.email},
        ):
            user = MontrekOIDCAuthenticationBackend().get_or_create_user(
                "access-token", None, None
            )
        self.assertEqual(user, known)

    @override_settings(
        OIDC_ISSUER_URL="",
        PROJECT_NAME="default",
        DEPLOY_HOST="example.com",
        KEYCLOAK_REALM="r",
        OIDC_OP_TOKEN_ENDPOINT="https://kc/token",  # nosec B106: a URL
        OIDC_OP_USER_ENDPOINT="https://kc/userinfo",
        OIDC_OP_JWKS_ENDPOINT="https://kc/certs",
    )
    def test_without_issuer_url_users_are_linked_to_the_keycloak_realm(self):
        user = self.sign_in()
        self.assertEqual(user.oidc_issuer, "https://auth-default.example.com/realms/r")


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

    def derived_user(self, provider_email):
        # As mozilla-django-oidc created them: the password derived from the
        # email as the provider sent it, the email stored normalized.
        return get_user_model().objects.create_user(
            email=provider_email,
            password=default_username_algo(provider_email),
        )

    def test_removes_a_password_derived_from_a_lowercase_provider_email(self):
        user = self.derived_user("someone@example.com")

        self.migration.remove_derived_passwords(django_apps, None)

        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())

    def test_removes_a_password_derived_from_a_mixed_case_local_part(self):
        user = self.derived_user("Someone@example.com")

        self.migration.remove_derived_passwords(django_apps, None)

        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())

    def test_cannot_recover_an_uppercase_domain(self):
        # The domain's casing is lost when the email is stored, so this
        # password stays. The limit the migration documents; Keycloak sends
        # lowercase emails, and users created from now on get no password.
        user = self.derived_user("someone@Example.com")
        self.assertEqual(user.email, "someone@example.com")

        self.migration.remove_derived_passwords(django_apps, None)

        user.refresh_from_db()
        self.assertTrue(
            user.check_password(default_username_algo("someone@Example.com"))
        )

    def test_spells_the_library_algorithm(self):
        email = "Someone@Example.com"
        self.assertEqual(
            self.migration.derived_password(email), default_username_algo(email)
        )


@override_settings(**OIDC_SETTINGS, OIDC_ROLES_CLAIM="roles", OIDC_STAFF_ROLE="Admin")
class TestRolesFromTheProvider(TestCase):
    subject = "subject-1"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            oidc_issuer=oidc_mocks.ISSUER_URL,
            oidc_subject=self.subject,
        )
        self.readers = GroupFactory(name="Readers")
        self.writers = GroupFactory(name="Writers")

    def sign_in(self, payload, user=None):
        user = user or self.user
        claims = {"sub": user.oidc_subject, "email": user.email}
        with mock.patch.object(
            OIDCAuthenticationBackend, "get_userinfo", return_value=claims
        ):
            signed_in = MontrekOIDCAuthenticationBackend().get_or_create_user(
                "access-token", "id-token", {"sub": user.oidc_subject, **payload}
            )
        signed_in.refresh_from_db()
        return signed_in

    def group_names(self, user):
        return set(user.groups.values_list("name", flat=True))

    def test_the_roles_decide_the_groups(self):
        self.user.groups.add(self.writers)

        user = self.sign_in({"roles": ["Readers"]})

        self.assertEqual(self.group_names(user), {"Readers"})

    def test_a_role_without_a_group_is_ignored(self):
        with self.assertLogs("user.backends", "INFO"):
            user = self.sign_in({"roles": ["Readers", "Unknown"]})

        self.assertEqual(self.group_names(user), {"Readers"})

    def test_without_roles_the_user_is_in_no_group_and_no_staff(self):
        # Entra ID leaves the claim out for a user without roles.
        self.user.groups.add(self.readers)
        self.user.is_staff = True
        self.user.save()

        user = self.sign_in({})

        self.assertEqual(self.group_names(user), set())
        self.assertFalse(user.is_staff)

    def test_the_staff_role_makes_staff(self):
        user = self.sign_in({"roles": ["Admin", "Writers"]})

        self.assertTrue(user.is_staff)
        self.assertEqual(self.group_names(user), {"Writers"})

    def test_the_staff_role_also_grants_its_group(self):
        GroupFactory(name="Admin")

        user = self.sign_in({"roles": ["Admin"]})

        self.assertTrue(user.is_staff)
        self.assertEqual(self.group_names(user), {"Admin"})

    def test_the_staff_role_is_not_logged_as_a_role_without_group(self):
        with self.assertNoLogs("user.backends", "INFO"):
            self.sign_in({"roles": ["Admin", "Readers"]})

    def test_a_revoking_sign_in_with_a_stale_user_revokes_staff(self):
        stale = get_user_model().objects.get(pk=self.user.pk)
        self.sign_in({"roles": ["Admin"]})

        MontrekOIDCAuthenticationBackend.assign_roles(stale, {"roles": []})

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(stale.is_staff)

    @override_settings(OIDC_STAFF_ROLE="")
    def test_without_a_staff_role_is_staff_stays_as_set_in_montrek(self):
        self.user.is_staff = True
        self.user.save()

        self.assertTrue(self.sign_in({"roles": []}).is_staff)

    @override_settings(OIDC_ROLES_CLAIM="")
    def test_without_a_roles_claim_the_groups_stay_as_set_in_montrek(self):
        self.user.groups.add(self.writers)

        user = self.sign_in({"roles": ["Readers"]})

        self.assertEqual(self.group_names(user), {"Writers"})

    def test_a_superuser_is_left_as_it_is(self):
        admin = get_user_model().objects.create_superuser(
            "admin@example.com", "a password"  # nosec B106: test password
        )
        admin.oidc_issuer, admin.oidc_subject = oidc_mocks.ISSUER_URL, "admin"
        admin.save()
        admin.groups.add(self.writers)

        admin = self.sign_in({"roles": []}, user=admin)

        self.assertTrue(admin.is_staff)
        self.assertEqual(self.group_names(admin), {"Writers"})

    def test_a_roles_claim_that_is_no_list_is_refused(self):
        with self.assertRaises(SuspiciousOperation):
            self.sign_in({"roles": "Readers"})

    def test_a_rest_api_token_leaves_the_roles_alone(self):
        self.user.groups.add(self.writers)
        with mock.patch.object(
            OIDCAuthenticationBackend,
            "get_userinfo",
            return_value={"sub": self.subject, "email": self.user.email},
        ):
            MontrekOIDCAuthenticationBackend().get_or_create_user(
                "access-token", None, None
            )
        self.assertEqual(self.group_names(self.user), {"Writers"})
