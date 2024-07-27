from testing.decorators import add_logged_in_user
from user.models import MontrekUser
from django.test import TestCase


class TestAddLoggedInUser(TestCase):

    @add_logged_in_user
    def setUp(self):
        pass

    def test_add_logged_in_user(self):
        self.assertIsInstance(self.user, MontrekUser)
        self.assertTrue(self.user.is_authenticated)
