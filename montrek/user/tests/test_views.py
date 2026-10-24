from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from montrek.utils import get_keycloak_base_url, get_oidc_endpoints
from user import views
from user.tests import oidc_mocks


def _get_messages_from_response(response):
    return list(response.context["messages"])


class TestMontrekSignUpView(TestCase):
    def test_signup_view(self):
        url = reverse("signup")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_signup_form_submission(self):
        url = reverse("signup")
        data = {
            "email": "test@example.com",
            "password1": "testpassword",  # nosec: B106: Testpasswort
            "password2": "testpassword",  # nosec: B106: Testpasswort
        }

        response = self.client.post(url, data, follow=True)
        messages = list(response.context["messages"])

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))

        self.assertTrue(
            get_user_model().objects.filter(email="test@example.com").exists()
        )
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You have logged in as test@example.com!")
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You have logged in as test@example.com!")

    def test_signup_form_invalid_submission(self):
        url = reverse("signup")
        data = {
            "email": "invalid-email",
            "password1": "testpassword",  # nosec: B106: Testpasswort
            "password2": "testpassword",  # nosec: B106: Testpasswort
        }

        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Email: Enter a valid email address.")


class TestMontrekLoginView(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

    def test_login_view(self):
        url = reverse("login")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_login_form_submission(self):
        url = reverse("login")
        data = {
            "username": "test@example.com",
            "password": "testpassword",  # nosec: B106: Testpasswort
        }

        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You have logged in as test@example.com!")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_form_invalid_submission(self):
        url = reverse("login")
        data = {
            "username": "nonexistent",
            "password": "testpassword",  # nosec: B106: Testpasswort
        }

        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
        self.assertContains(
            response, "Please enter a correct email address and password."
        )
        self.assertEqual(
            str(messages[0]),
            "All: Please enter a correct email address and password. Note that both fields may be case-sensitive.",
        )


class TestMontrekLogoutView(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

    def test_logout_view(self):
        url = reverse("logout")
        response = self.client.post(url)

        self.assertRedirects(response, reverse("login"))


class TestMontrekPasswordResetView(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

    def test_password_reset_view(self):
        url = reverse("password_reset")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_password_reset_form_submission(self):
        url = reverse("password_reset")
        data = {
            "email": "test@example.com",
        }
        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)
        message = str(messages[0])

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            message,
            "We've emailed you instructions for setting your password. You should receive the email shortly!",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Password reset on testserver")

    def test_password_reset_form_invalid_submission(self):
        url = reverse("password_reset")
        data = {
            "email": "test",
        }
        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)
        message = str(messages[0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(messages), 1)
        self.assertEqual(message, "Email: Enter a valid email address.")

    def test_password_reset_form_unknown_email(self):
        url = reverse("password_reset")
        data = {
            "email": "foo@bar.com",
        }
        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)
        message = str(messages[0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            message,
            "Email: This email address doesn't have an associated user account.",
        )


class TestMontrekPasswordResetCompleteView(TestCase):
    def test_password_reset_complete_view(self):
        url = reverse("password_reset_complete")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("login"))


class TestMontrekPasswordChangeView(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

    def test_password_change_view(self):
        self.client.login(
            email="test@example.com", password="testpassword"
        )  # nosec: B106: Testpasswort
        url = reverse("password_change")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_password_change_form_submission(self):
        self.client.login(
            email="test@example.com", password="testpassword"
        )  # nosec: B106: Testpasswort
        url = reverse("password_change")
        data = {
            "old_password": "testpassword",
            "new_password1": "!@#$hardt0guess",  # nosec: B106: Testpasswort
            "new_password2": "!@#$hardt0guess",  # nosec: B106: Testpasswort
        }
        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)
        message = str(messages[0])
        self.user.refresh_from_db()

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(message, "Your password has been changed.")
        self.assertTrue(self.user.check_password("!@#$hardt0guess"))

    def test_password_change_form_invalid_submission(self):
        self.client.login(
            email="test@example.com", password="testpassword"
        )  # nosec: B106: Testpasswort
        url = reverse("password_change")
        data = {
            "old_password": "invalid",
            "new_password1": "!@#$hardt0guess",
            "new_password2": "!@#$hardt0guess",
        }
        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)
        message = str(messages[0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            message,
            "Oldpassword: Your old password was entered incorrectly. Please enter it again.",
        )

    def test_password_change_view_anonymous(self):
        url = reverse("password_change")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('password_change')}",
        )

    def test_password_change_form_submission_anonymous(self):
        url = reverse("password_change")
        data = {
            "old_password": "testpassword",
            "new_password1": "!@#$hardt0guess",  # nosec: B106: Testpasswort
            "new_password2": "!@#$hardt0guess",  # nosec: B106: Testpasswort
        }
        response = self.client.post(url, data)

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('password_change')}"
        )


class TestKeycloakSettings(TestCase):
    @override_settings(
        ENABLE_KEYCLOAK=True,
        DEPLOY_HOST="test-host.de",
        PROJECT_NAME="test-project",
        KEYCLOAK_PORT="8080",
        KEYCLOAK_REALM="test-realm",
    )
    def test_keycloak_settings(self):
        keycloak_base = get_keycloak_base_url()
        self.assertEqual(
            keycloak_base, "https://auth-test-project.test-host.de/realms/test-realm"
        )
        oicd_endpoints = get_oidc_endpoints()

        self.assertEqual(
            oicd_endpoints["authorization"],
            keycloak_base + "/protocol/openid-connect/auth",
        )
        self.assertEqual(
            oicd_endpoints["token"],
            keycloak_base + "/protocol/openid-connect/token",
        )
        self.assertEqual(
            oicd_endpoints["userinfo"],
            keycloak_base + "/protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            oicd_endpoints["jwks"],
            keycloak_base + "/protocol/openid-connect/certs",
        )
        self.assertEqual(
            oicd_endpoints["logout"],
            keycloak_base + "/protocol/openid-connect/logout",
        )


@override_settings(
    ENABLE_OIDC=True,
    OIDC_ISSUER_URL=oidc_mocks.ISSUER_URL,
    OIDC_RP_CLIENT_ID="montrek",
)
class TestOidcLogin(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

    def test_login_redirects_to_the_discovered_authorization_endpoint(self):
        request = RequestFactory().get("/oidc/authenticate/")
        SessionMiddleware(lambda request: None).process_request(request)
        with mock.patch(
            oidc_mocks.REQUESTS_GET, return_value=oidc_mocks.discovery_response()
        ):
            response = views.MontrekOIDCAuthenticationRequestView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        location = urlparse(response.url)
        self.assertEqual(
            f"{location.scheme}://{location.netloc}{location.path}",
            "https://login.example.com/tenant/authorize",
        )
        self.assertEqual(parse_qs(location.query)["client_id"], ["montrek"])

    def test_logout_ends_the_session_at_the_provider(self):
        self.client.force_login(self.user)
        with mock.patch(
            oidc_mocks.REQUESTS_GET, return_value=oidc_mocks.discovery_response()
        ):
            response = self.client.post(reverse("logout"))

        self.assertRedirects(
            response,
            "https://login.example.com/tenant/logout",
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_without_reachable_provider_logs_out_of_montrek(self):
        self.client.force_login(self.user)
        with (
            mock.patch(oidc_mocks.REQUESTS_GET, side_effect=oidc_mocks.unreachable()),
            self.assertLogs("user.modules.oidc_provider", "ERROR"),
        ):
            response = self.client.post(reverse("logout"), follow=True)

        self._assert_logged_out_without_new_login(response)

    def test_logout_without_end_session_endpoint_does_not_log_in_again(self):
        document = {**oidc_mocks.DISCOVERY_DOCUMENT}
        del document["end_session_endpoint"]
        self.client.force_login(self.user)
        with mock.patch(
            oidc_mocks.REQUESTS_GET,
            return_value=oidc_mocks.discovery_response(document),
        ):
            response = self.client.post(reverse("logout"), follow=True)

        self._assert_logged_out_without_new_login(response)

    def _assert_logged_out_without_new_login(self, response):
        self.assertEqual(response.redirect_chain, [(reverse("logged_out"), 302)])
        # The page is shown instead of the login, which would start the login
        # at the provider again.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/logged_out.html")
        self.assertContains(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(ALLOW_SIGNUP=False)
class TestSignUpClosed(TestCase):
    def test_signup_is_not_found(self):
        response = self.client.post(
            reverse("signup"),
            {
                "email": "new@example.com",
                "password1": "!@#$hardt0guess",  # nosec: B106: Testpasswort
                "password2": "!@#$hardt0guess",  # nosec: B106: Testpasswort
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            get_user_model().objects.filter(email="new@example.com").exists()
        )

    def test_navbar_does_not_link_to_signup(self):
        response = self.client.get(reverse("logged_out"))

        self.assertNotContains(response, reverse("signup"))


@override_settings(
    ENABLE_OIDC=True,
    OIDC_ISSUER_URL=oidc_mocks.ISSUER_URL,
    OIDC_RP_CLIENT_ID="montrek",
    OIDC_RP_CLIENT_SECRET="",  # nosec: B106: public test client
    ALLOW_PASSWORD_LOGIN=False,
    ALLOW_SIGNUP=False,
    LOGIN_URL="/oidc/authenticate/",
    AUTHENTICATION_BACKENDS=("user.backends.MontrekOIDCAuthenticationBackend",),
)
class TestOidcOnlySignIn(TestCase):
    password = "testpassword"  # noqa: S105 # nosec: B105: Testpasswort

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password=self.password
        )

    def test_password_form_is_not_accepted(self):
        response = self.client.post(
            reverse("login"), {"username": self.user.email, "password": self.password}
        )

        self.assertEqual(response.status_code, 405)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_pages_are_not_found(self):
        for url in (
            reverse("password_reset"),
            reverse("password_reset_complete"),
            reverse("password_reset_confirm", kwargs={"uidb64": "MQ", "token": "x-y"}),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_password_change_is_not_found(self):
        self.client.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("password_change"))

        self.assertEqual(response.status_code, 404)

    def test_tokens_are_not_issued_for_a_password(self):
        for name, data in (
            (
                "token_obtain_pair",
                {"email": self.user.email, "password": self.password},
            ),
            ("token_refresh", {"refresh": "x"}),
            ("token_verify", {"token": "x"}),
        ):
            with self.subTest(name=name):
                response = self.client.post(reverse(name), data)
                self.assertEqual(response.status_code, 404)

    def test_admin_login_goes_to_the_provider(self):
        response = self.client.get(reverse("admin:login"))

        self.assertRedirects(
            response,
            f"/oidc/authenticate/?next={reverse('admin:index')}",
            fetch_redirect_response=False,
        )

    def test_admin_pages_go_to_the_provider(self):
        changelist = reverse("admin:auth_group_changelist")

        to_login = self.client.get(changelist)
        to_provider = self.client.get(to_login.url)

        self.assertRedirects(
            to_provider,
            f"/oidc/authenticate/?next={changelist}",
            fetch_redirect_response=False,
        )

    def test_admin_login_for_a_signed_in_user_stays_in_the_admin(self):
        # No staff member: the admin says so instead of sending the user to the
        # provider, which would sign them in and send them back here.
        self.client.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/login.html")

    def test_admin_login_does_not_accept_the_password(self):
        self.user.is_staff = True
        self.user.save()

        self.client.post(
            reverse("admin:login"),
            {"username": self.user.email, "password": self.password},
        )

        self.assertNotIn("_auth_user_id", self.client.session)

    def test_navbar_does_not_link_to_password_pages(self):
        self.client.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, reverse("password_change"))
        self.assertNotContains(response, reverse("signup"))


@override_settings(
    ENABLE_OIDC=True,
    OIDC_ISSUER_URL=oidc_mocks.ISSUER_URL,
    OIDC_RP_CLIENT_ID="montrek",
    OIDC_RP_CLIENT_SECRET="",  # nosec: B106: public test client
    ALLOW_PASSWORD_LOGIN=True,
    LOGIN_URL="/oidc/authenticate/",
    AUTHENTICATION_BACKENDS=(
        "user.backends.MontrekOIDCAuthenticationBackend",
        "django.contrib.auth.backends.ModelBackend",
    ),
)
class TestOidcWithPasswordFallback(TestCase):
    def test_admin_login_accepts_the_password(self):
        get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpassword",  # nosec: B106: Testpasswort
        )

        response = self.client.post(
            reverse("admin:login"),
            {
                "username": "admin@example.com",
                "password": "testpassword",
                "next": reverse("admin:index"),
            },
        )

        self.assertRedirects(
            response, reverse("admin:index"), fetch_redirect_response=False
        )
        self.assertIn("_auth_user_id", self.client.session)
