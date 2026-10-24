from django.test import TestCase, override_settings
from django.urls import reverse
from middleware.login_required_middleware import is_login_exempt_path
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestLoginRequiredMiddleware(TestCase):
    def test_startpage_redirects_to_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/home")

    def test_middleware_redirects_to_login_page(self):
        response = self.client.get("/home")
        self.assertRedirects(response, reverse("login"))

    def test_middleware_does_not_redirect_for_authenticated_user(self):
        user = MontrekUserFactory()
        self.client.force_login(user)
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_middleware_does_not_redirect_for_exempt_path(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_EXEMPT_PATHS=[r"^montrek_example/a/.*$"])
    def test_middleware_does_not_redirect_for_exempt_path__sub_path(self):
        response = self.client.get(reverse("montrek_example_a_list"))
        self.assertEqual(response.status_code, 200)


class TestUserPagesExemption(TestCase):
    def test_pages_for_signed_out_users_are_exempt(self):
        for url in (
            reverse("signup"),
            reverse("login"),
            reverse("logout"),
            reverse("logged_out"),
            reverse("password_reset"),
            reverse("password_reset_confirm", kwargs={"uidb64": "MQ", "token": "x-y"}),
            reverse("password_reset_complete"),
            "/user/oidc/authenticate/",
            "/user/oidc/callback/",
            "/user/oidc/logout/",
        ):
            with self.subTest(url=url):
                self.assertTrue(is_login_exempt_path(url))

    def test_other_user_pages_need_the_login(self):
        for url in (
            reverse("password_change"),
            "/user/",
            "/user/new_page/",
            "/user/login/extra",
            "/user/signup/x/",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_login_exempt_path(url))
