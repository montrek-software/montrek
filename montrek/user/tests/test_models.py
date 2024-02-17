from django.test import TestCase
from django.contrib.auth import get_user_model
from user import models as user_models
from django.contrib.auth import models as auth_models


class TestMontrekUser(TestCase):
    def test_is_active_auth_user_model(self):
        self.assertEqual(get_user_model(), user_models.MontrekUser)

    def test_is_abstract_base_user(self):
        self.assertTrue(issubclass(user_models.MontrekUser, auth_models.AbstractUser))

    def test_manager_is_base_user_manager(self):
        self.assertTrue(
            issubclass(user_models.MontrekUserManager, auth_models.BaseUserManager)
        )

    def test_create_user(self):
        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword"
        )
        db_users = get_user_model().objects.all()

        self.assertEqual(len(db_users), 1)
        self.assertEqual(db_users[0], user)
        self.assertFalse(user.is_staff)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError) as e:
            get_user_model().objects.create_user(email="", password="testpassword")

        self.assertEqual(str(e.exception), "User must have an email address.")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com", password="testpassword"
        )
        db_users = get_user_model().objects.all()

        self.assertEqual(len(db_users), 1)
        self.assertEqual(db_users[0], user)
        self.assertTrue(user.is_staff)

    def test_user_str(self):
        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword"
        )
        self.assertEqual(str(user), "test@example.com")
