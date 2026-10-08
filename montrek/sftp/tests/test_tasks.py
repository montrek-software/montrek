from unittest import mock

from django.test import TestCase

from sftp.managers.sftp_import_manager import SftpSyncResult
from sftp.tasks import sftp_import_source_sync_task, sftp_poll_active_sources_task
from sftp.tests.factories.sftp_import_source_factories import (
    SftpImportSourceSatelliteFactory,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestSftpTasks(TestCase):
    def setUp(self):
        self.superuser = MontrekUserFactory(is_superuser=True)
        self.active = SftpImportSourceSatelliteFactory(is_active=True)
        self.inactive = SftpImportSourceSatelliteFactory(is_active=False)

    def test_sync_task_polls_given_source(self):
        with mock.patch("sftp.tasks.SftpImportManager") as manager_class:
            manager_class.return_value.sync.return_value = SftpSyncResult()
            message = sftp_import_source_sync_task.run(
                source_hub_id=self.inactive.hub_entity_id, user_id=7
            )
        manager_class.assert_called_once_with(
            {"pk": self.inactive.hub_entity_id, "user_id": 7}
        )
        self.assertEqual(message, "No new files")

    def test_poll_task_polls_active_sources_only(self):
        with mock.patch("sftp.tasks.SftpImportManager") as manager_class:
            manager_class.return_value.sync.return_value = SftpSyncResult(
                imported=["a.csv"]
            )
            message = sftp_poll_active_sources_task.run()
        manager_class.assert_called_once_with({"pk": self.active.hub_entity_id})
        self.assertEqual(
            message, f"{self.active.hub_entity_id}: Imported 1 file(s): a.csv"
        )

    def test_poll_task_without_sources(self):
        self.active.is_active = False
        self.active.save()
        self.assertEqual(
            sftp_poll_active_sources_task.run(), "No active SFTP import sources"
        )
