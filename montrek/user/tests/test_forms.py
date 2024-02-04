from django.test import TestCase
from user.models import MontrekUser
from user.forms import MontrekUserCreationForm
from django.contrib.auth.forms import UserCreationForm

class TestMontrekUserCreationForm:

    def test_is_user_creation_form(self):
        self.assertTrue(issubclass(MontrekUserCreationForm, UserCreationForm))

    def test_model_is_montrek_user(self):
        self.assertEqual(MontrekUserCreationForm.Meta.model, MontrekUser)

    def test_model_fields(self):
        self.assertEqual(MontrekUserCreationForm.Meta.fields, UserCreationForm.Meta.fields)
