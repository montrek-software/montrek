from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.test import TestCase
from django.urls import reverse


def _get_messages_from_response(response):
    return list(response.context["messages"])


class MontrekSignUpViewTests(TestCase):
    def test_signup_view(self):
        url = reverse("signup")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_signup_form_submission(self):
        url = reverse("signup")
        data = {
            "email": "test@example.com",
            "password1": "testpassword",
            "password2": "testpassword",
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

    def test_signup_form_invalid_submission(self):
        url = reverse("signup")
        data = {
            "email": "invalid-email",
            "password1": "testpassword",
            "password2": "testpassword",
        }

        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Email: Enter a valid email address.")


class MontrekLoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",
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
            "password": "testpassword",
        }

        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You have logged in as test@example.com!")

    def test_login_form_invalid_submission(self):
        url = reverse("login")
        data = {
            "username": "nonexistent",
            "password": "testpassword",
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


class MontrekLogoutViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",
        )

    def test_logout_view(self):
        url = reverse("logout")
        response = self.client.get(url)

        self.assertRedirects(response, reverse("home"))


class MontrekPasswordResetViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",
        )

    def test_password_reset_view(self):
        url = reverse("password_reset")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
