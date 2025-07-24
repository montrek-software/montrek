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
