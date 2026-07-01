from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from testing.test_cases.view_test_cases import TEST_USER_PASSWORD
from user import models as user_models
from user.tests.factories import MontrekUserFactory, UserAssignmentSatelliteFactory


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
            email="test@example.com", password=TEST_USER_PASSWORD
        )
        db_users = get_user_model().objects.all()

        self.assertEqual(len(db_users), 1)
        self.assertEqual(db_users[0], user)
        self.assertFalse(user.is_staff)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError) as e:
            get_user_model().objects.create_user(email="", password=TEST_USER_PASSWORD)

        self.assertEqual(str(e.exception), "User must have an email address.")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com", password=TEST_USER_PASSWORD
        )
        db_users = get_user_model().objects.all()

        self.assertEqual(len(db_users), 1)
        self.assertEqual(db_users[0], user)
        self.assertTrue(user.is_staff)

    def test_user_str(self):
        user = get_user_model().objects.create_user(
            email="test@example.com", password=TEST_USER_PASSWORD
        )
        self.assertEqual(str(user), "test@example.com")


class TestUserAssignmentSignal(TestCase):
    def test_creates_hub_and_satellite_on_user_creation(self):
        user = MontrekUserFactory()
        self.assertEqual(
            user_models.UserAssignmentSatellite.objects.filter(user=user).count(), 1
        )
        sat = user_models.UserAssignmentSatellite.objects.get(user=user)
        self.assertIsNotNone(sat.hub_entity)

    def test_creates_hub_value_date_on_user_creation(self):
        user = MontrekUserFactory()
        sat = user_models.UserAssignmentSatellite.objects.get(user=user)
        hub = sat.hub_entity
        self.assertEqual(hub.hub_value_date.count(), 1)

    def test_signal_is_idempotent(self):
        user = MontrekUserFactory()
        user.save()
        user.save()
        self.assertEqual(
            user_models.UserAssignmentSatellite.objects.filter(user=user).count(), 1
        )

    def test_hub_str_returns_user_email(self):
        user = MontrekUserFactory()
        sat = user_models.UserAssignmentSatellite.objects.get(user=user)
        self.assertEqual(str(sat.hub_entity), user.email)


class TestUserAssignmentModels(TestCase):
    def test_satellite_identifier_fields(self):
        self.assertEqual(
            user_models.UserAssignmentSatellite.identifier_fields, ["user_id"]
        )

    def test_satellite_factory_creates_hub_and_satellite(self):
        sat = UserAssignmentSatelliteFactory()
        self.assertIsNotNone(sat.hub_entity_id)
        self.assertIsNotNone(sat.user_id)
