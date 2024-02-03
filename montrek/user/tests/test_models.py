from django.test import TestCase
from django.contrib.auth import get_user_model
from user.models import MontrekUser, MontrekUserManager
from django.contrib.auth.models import AbstractUser, BaseUserManager

class TestMontrekUser(TestCase):

    def test_montrek_user_is_active_auth_user_model(self):
        self.assertEqual(get_user_model(), MontrekUser)

    def test_montrek_user_is_abstract_base_user(self):
        self.assertTrue(issubclass(MontrekUser, AbstractUser))

    def test_montrek_user_manager_is_base_user_manager(self):
        self.assertTrue(issubclass(MontrekUserManager, BaseUserManager))
