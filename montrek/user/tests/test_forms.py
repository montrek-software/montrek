from django.test import TestCase
from user.models import MontrekUser
from user import forms as user_forms
from django.contrib.auth import forms as auth_forms


class TestMontrekUserCreationForm(TestCase):
    def test_is_user_creation_form(self):
        self.assertTrue(
            issubclass(
                user_forms.MontrekUserCreationForm, auth_forms.BaseUserCreationForm
            )
        )

    def test_model_is_montrek_user(self):
        self.assertEqual(user_forms.MontrekUserCreationForm.Meta.model, MontrekUser)


class TestMontrekPasswordResetForm(TestCase):
    def test_is_user_creation_form(self):
        self.assertTrue(
            issubclass(
                user_forms.MontrekPasswordResetForm, auth_forms.PasswordResetForm
            )
        )


class TestMontrekUserChangeForm(TestCase):
    def test_is_user_creation_form(self):
        self.assertTrue(
            issubclass(user_forms.MontrekUserChangeForm, auth_forms.UserChangeForm)
        )


class TestMontrekAuthenticationForm(TestCase):
    def test_is_user_creation_form(self):
        self.assertTrue(
            issubclass(
                user_forms.MontrekAuthenticationForm, auth_forms.AuthenticationForm
            )
        )


class TestMontrekPasswordChangeForm(TestCase):
    def test_is_user_creation_form(self):
        self.assertTrue(
            issubclass(
                user_forms.MontrekPasswordChangeForm, auth_forms.PasswordChangeForm
            )
        )
