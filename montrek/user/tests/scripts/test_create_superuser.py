from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from user.scripts.create_superuser import run


class TestCreateSuperUser(TestCase):
    @override_settings(ADMIN_NAME=None)
    def test_no_admin_name(self):
        self.assertRaisesMessage(run, "No ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD set")

    @override_settings(ADMIN_EMAIL=None)
    def test_no_admin_email(self):
        self.assertRaisesMessage(run, "No ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD set")

    @override_settings(ADMIN_PASSWORD=None)
    def test_no_admin_password(self):
        self.assertRaisesMessage(run, "No ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD set")

    def test_create_super_user(self):
        user = get_user_model()
        # Check that admin superuser has not been created
        admin_query = user.objects.filter(email="test@admin.de")
        self.assertEqual(admin_query.count(), 0)
        run()
        admin_query = user.objects.filter(email="test@admin.de")
        self.assertEqual(admin_query.count(), 1)
        admin = admin_query.first()
        self.assertEqual(admin.email, "test@admin.de")
        self.assertTrue(
            admin.password.startswith(
                "pbkdf2_sha256$",
            )
        )
        run()
