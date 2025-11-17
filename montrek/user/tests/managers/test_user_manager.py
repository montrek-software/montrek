from django.contrib.auth import get_user_model
from django.test import TestCase
from user.managers.user_manager import UserManager


class TestMontrekUserManager(TestCase):
    def test_get_superuser(self):
        user_manager = UserManager({})
        no_superuser = user_manager.get_superuser()
        self.assertIsNone(no_superuser)
        get_user_model().objects.create_superuser(
            email="test@example.com",
            password="testpassword",  # nosec
        )
        superuser = user_manager.get_superuser()
        self.assertIsNotNone(superuser)
