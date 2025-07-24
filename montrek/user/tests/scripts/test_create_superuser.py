from django.test import TestCase
from user.scripts.create_superuser import run


class TestCreateSuperUser(TestCase):
    def test_create_super_user(self):
        run()
