from typing import cast

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import resolve, reverse

from baseclasses.access import permissions_for_callback
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository
from sftp.tests.factories.sftp_connection_hub_factories import (
    SftpConnectionHubValueDateFactory,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
)
from sftp.user_groups.constants import SftpPermissions, SftpUserGroups
from user.managers.user_group_manager import create_groups
from user.models import MontrekUser
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestSftpAccess(TestCase):
    def setUp(self):
        create_groups(SftpUserGroups)
        self.hub_vd = SftpConnectionHubValueDateFactory(value_date=None)
        SftpConnectionSatelliteFactory(
            hub_entity=self.hub_vd.hub, host="sftp.example.com"
        )
        SftpCredentialSatelliteFactory(hub_entity=self.hub_vd.hub)
        self.read_urls = [
            reverse("sftp_connection_list"),
            reverse("sftp_connection_details", kwargs={"pk": self.hub_vd.hub.pk}),
            reverse("sftp_connection_history", kwargs={"pk": self.hub_vd.pk}),
        ]
        self.write_urls = [
            reverse("sftp_connection_create"),
            reverse("sftp_connection_update", kwargs={"pk": self.hub_vd.pk}),
            reverse("sftp_connection_delete", kwargs={"pk": self.hub_vd.pk}),
        ]

    def _login(self, *group_enums: SftpUserGroups):
        user = cast(MontrekUser, MontrekUserFactory())
        user.groups.set(
            Group.objects.filter(name__in=[group.group_name for group in group_enums])
        )
        self.client.force_login(user)

    def _assert_denied(self, url: str):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, url)
        self.assertNotContains(response, "sftp.example.com", status_code=302)

    def test_each_view_requires_its_permission(self):
        expected = {
            "sftp_connection": SftpPermissions.CAN_VIEW,
            "sftp_connection_list": SftpPermissions.CAN_VIEW,
            "sftp_connection_details": SftpPermissions.CAN_VIEW,
            "sftp_connection_history": SftpPermissions.CAN_VIEW,
            "sftp_connection_create": SftpPermissions.CAN_CREATE,
            "sftp_connection_update": SftpPermissions.CAN_UPDATE,
            "sftp_connection_delete": SftpPermissions.CAN_DELETE,
            "sftp_import_source_list": SftpPermissions.CAN_VIEW,
            "sftp_import_source_details": SftpPermissions.CAN_VIEW,
            "sftp_import_source_imported_files": SftpPermissions.CAN_VIEW,
            "sftp_import_source_history": SftpPermissions.CAN_VIEW,
            "sftp_import_source_create": SftpPermissions.CAN_CREATE,
            "sftp_import_source_update": SftpPermissions.CAN_UPDATE,
            "sftp_import_source_sync": SftpPermissions.CAN_UPDATE,
            "sftp_import_source_delete": SftpPermissions.CAN_DELETE,
        }
        for url_name, permission in expected.items():
            with self.subTest(url_name=url_name):
                kwargs = (
                    {}
                    if url_name.endswith(("connection", "list", "create"))
                    else {"pk": 1}
                )
                callback = resolve(reverse(url_name, kwargs=kwargs)).func
                self.assertEqual(
                    permissions_for_callback(callback),
                    (permission.namespaced_codename,),
                )

    def test_user_without_sftp_group_is_denied(self):
        self._login()
        for url in self.read_urls + self.write_urls:
            with self.subTest(url=url):
                self._assert_denied(url)

    def test_viewer_can_read_but_not_change(self):
        self._login(SftpUserGroups.VIEWER)
        for url in self.read_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for url in self.write_urls:
            with self.subTest(url=url):
                self._assert_denied(url)

    def test_viewer_cannot_delete_by_post(self):
        self._login(SftpUserGroups.VIEWER)
        self.client.post(
            reverse("sftp_connection_delete", kwargs={"pk": self.hub_vd.pk})
        )
        self.assertEqual(SftpConnectionRepository().receive().count(), 1)

    def test_admin_can_use_every_view(self):
        self._login(SftpUserGroups.ADMIN)
        for url in self.read_urls + self.write_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
