from django.test import TestCase, override_settings
from django.urls import reverse
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


class TestLoginRequiredMiddlewareRestRequests(TestCase):
    def test_rest_request_to_a_page_needs_the_login(self):
        for url in (reverse("home"), reverse("montrek_example_a_create")):
            with self.subTest(url=url):
                response = self.client.get(url, {"gen_rest_api": "true"})
                self.assertRedirects(
                    response, reverse("login"), fetch_redirect_response=False
                )

    def test_percent_encoded_rest_request_to_a_page_needs_the_login(self):
        response = self.client.get(
            reverse("home") + "?%67en%5Frest%5Fapi=%74rue",
        )

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_rest_request_to_an_unknown_path_needs_the_login(self):
        response = self.client.get("/no/such/page", {"gen_rest_api": "true"})

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_rest_request_to_an_api_view_is_left_to_the_view(self):
        # The view asks for a bearer token rather than sending to the login.
        response = self.client.get(
            reverse("montrek_example_a_list"), {"gen_rest_api": "true"}
        )

        self.assertEqual(response.status_code, 401)

    def test_api_view_page_needs_the_login(self):
        response = self.client.get(reverse("montrek_example_a_list"))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_rest_only_view_is_left_to_the_view(self):
        response = self.client.get(reverse("hub_a_rest_api"))

        self.assertEqual(response.status_code, 401)
