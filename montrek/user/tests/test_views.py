from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.test import TestCase
from django.urls import reverse


def _get_messages_from_response(response):
    return list(response.context["messages"])

class SignUpViewTests(TestCase):
    def test_signup_view(self):
        url = reverse("signup")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_signup_form_submission(self):
        url = reverse("signup")
        data = {
            "username": "testuser",
            "password1": "testpassword",
            "password2": "testpassword",
        }

        response = self.client.post(url, data, follow=True)
        messages = list(response.context["messages"])

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))

        self.assertTrue(get_user_model().objects.filter(username="testuser").exists())
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "You have logged in as testuser!"
        )

    def test_signup_form_invalid_submission(self):
        url = reverse("signup")
        data = {
            "username": "invalid-username!",
            "password1": "testpassword",
            "password2": "testpassword",
        }

        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
        self.assertContains(response, "Enter a valid username.")
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Username: Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
        )


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
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
            "username": "testuser",
            "password": "testpassword",
        }

        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "You have logged in as testuser!"
        )

    def test_login_form_invalid_submission(self):
        url = reverse("login")
        data = {
            "username": "nonexistent-user",
            "password": "testpassword",
        }

        response = self.client.post(url, data)
        messages = _get_messages_from_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")
        self.assertContains(response, "Please enter a correct username and password.")
        self.assertEqual(
            str(messages[0]),
            "All: Please enter a correct username and password. Note that both fields may be case-sensitive."
        )
