from django.test import TestCase
from user.models import MontrekUser
from user.admin import MontrekUserAdmin
from django.contrib.auth.admin import UserAdmin


class TestMontrekUserAdmin(TestCase):

    def test_montrek_user_admin_is_user_admin(self):
        self.assertTrue(issubclass(MontrekUserAdmin, UserAdmin))

    def test_montrek_user_admin_model_is_montrek_user(self):
        self.assertTrue(
            MontrekUserAdmin.model == MontrekUser
        )
