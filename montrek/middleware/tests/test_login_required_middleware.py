from django.test import TestCase, override_settings
from django.urls import reverse
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestLoginRequiredMiddleware(TestCase):
    def test_middleware_redirects_to_login_page(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("login"))

    def test_middleware_does_not_redirect_for_authenticated_user(self):
        user = MontrekUserFactory()
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_middleware_does_not_redirect_for_exempt_path(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_EXEMPT_PATHS=["/a/"])
    def test_middleware_does_not_redirect_for_exempt_path__sub_path(self):
        response = self.client.get(reverse("montrek_example_a_list"))
        self.assertEqual(response.status_code, 200)
