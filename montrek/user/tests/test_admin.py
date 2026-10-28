from django.test import TestCase
from django.urls import reverse
from user.models import MontrekUser
from user.admin import MontrekUserAdmin
from django.contrib.auth.admin import UserAdmin


class TestMontrekUserAdmin(TestCase):
    def test_is_user_admin(self):
        self.assertTrue(issubclass(MontrekUserAdmin, UserAdmin))

    def test_model_is_montrek_user(self):
        self.assertEqual(MontrekUserAdmin.model, MontrekUser)


class TestMontrekUserAdminKeepsUsers(TestCase):
    def setUp(self):
        self.admin = MontrekUser.objects.create_superuser(
            "admin@example.com",
            "testpassword",  # nosec: B106: Testpasswort
        )
        self.user = MontrekUser.objects.create_user(email="user@example.com")
        self.client.force_login(self.admin)

    def test_users_cannot_be_deleted(self):
        response = self.client.post(
            reverse("admin:user_montrekuser_delete", args=[self.user.pk]),
            {"post": "yes"},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertTrue(MontrekUser.objects.filter(pk=self.user.pk).exists())

    def test_user_list_offers_no_delete_action(self):
        response = self.client.get(reverse("admin:user_montrekuser_changelist"))

        self.assertNotContains(response, "delete_selected")

    def test_user_page_says_to_deactivate(self):
        response = self.client.get(
            reverse("admin:user_montrekuser_change", args=[self.user.pk])
        )

        self.assertContains(response, "Users are not deleted")
        self.assertNotContains(
            response, reverse("admin:user_montrekuser_delete", args=[self.user.pk])
        )
