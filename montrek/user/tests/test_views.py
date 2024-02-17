from decouple import RepositoryIni
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import mail
from django.core.mail import message
from django.test import TestCase
from django.urls import reverse


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


class TestMontrekLoginView(TestCase):
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
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

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


class TestMontrekLogoutView(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword",
        )

    def test_logout_view(self):
        url = reverse("logout")
        response = self.client.get(url)

        self.assertRedirects(response, reverse("login"))


class TestMontrekPasswordResetView(TestCase):
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

    def test_password_reset_form_submission(self):
        url = reverse("password_reset")
        data = {
            "email": "test@example.com",
        }
        response = self.client.post(url, data, follow=True)
        messages = _get_messages_from_response(response)
        message = str(messages[0])

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("home"))
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
            password="testpassword",
        )

    def test_password_change_view(self):
        self.client.login(email="test@example.com", password="testpassword")
        url = reverse("password_change")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_base.html")

    def test_password_change_form_submission(self):
        self.client.login(email="test@example.com", password="testpassword")
        url = reverse("password_change")
        data = {
            "old_password": "testpassword",
            "new_password1": "!@#$hardt0guess",
            "new_password2": "!@#$hardt0guess",
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
        self.client.login(email="test@example.com", password="testpassword")
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
            "new_password1": "!@#$hardt0guess",
            "new_password2": "!@#$hardt0guess",
        }
        response = self.client.post(url, data)

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('password_change')}"
        )
