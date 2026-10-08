import posixpath
import time
from typing import Any
from unittest import mock

import paramiko
from django.test import TestCase

from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.tests.mocks import MockFileUploadManager
from sftp.managers.sftp_import_manager import SftpImportManager
from sftp.models.sftp_import_source_sat_models import SftpImportSourceStatusSatellite
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportedFileRepository,
    SftpImportSourceRepository,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
)
from sftp.tests.factories.sftp_import_source_factories import (
    TEST_UPLOAD_TYPE,
    LinkSftpImportSourceSftpConnectionFactory,
    SftpImportSourceSatelliteFactory,
)
from sftp.tests.managers.test_sftp_client_manager import MTIME, FakeSftpClient
from user.tests.factories.montrek_user_factories import MontrekUserFactory

PollStatus = SftpImportSourceStatusSatellite.PollStatus

REMOTE_TREE = {
    "upload": {
        "a.csv": b"a,b\n1,2\n",
        "b.txt": b"text",
        "c.pdf": b"pdf content",
        "archive": {"old.csv": b"x"},
    },
}


class RecordingFileUploadManager(MockFileUploadManager):
    """Processes inline and remembers what it was handed."""

    do_process_file_async = False
    allow_unattended_upload = True
    unattended_accept = (".csv", ".txt")
    calls: list[dict[str, Any]] = []

    def upload_and_process(self, file) -> bool:
        RecordingFileUploadManager.calls.append(
            {
                "name": file.name,
                "content": file.read(),
                "session_data": dict(self.session_data),
                "pipeline_data": dict(self.pipeline_data),
            }
        )
        file.seek(0)
        return super().upload_and_process(file)


class RecordingWithDefaultsFileUploadManager(RecordingFileUploadManager):
    unattended_default_parameters = {"overwrite": False, "sheet": "Data"}


RECORDING_KEY = (
    "sftp.tests.managers.test_sftp_import_manager.RecordingFileUploadManager"
)


class FakeTimedSftpClient(FakeSftpClient):
    """Adds per-file modification times."""

    def __init__(self, tree: dict):
        super().__init__(tree)
        self.mtimes: dict[str, int] = {}

    def listdir_attr(self, path: str = ".") -> list[paramiko.SFTPAttributes]:
        entries = super().listdir_attr(path)
        directory = self._resolve(path)
        for attributes in entries:
            full_path = posixpath.join(directory, attributes.filename)
            attributes.st_mtime = self.mtimes.get(full_path, MTIME)
        return entries

    def put_file(self, path: str, content: bytes, mtime: int = MTIME) -> None:
        parent, name = posixpath.split(path)
        self._node(parent)[name] = content
        self.mtimes[path] = mtime


class SftpImportManagerTestCase(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.superuser = MontrekUserFactory(is_superuser=True)
        connection = SftpConnectionSatelliteFactory(base_path="/upload")
        SftpCredentialSatelliteFactory(hub_entity=connection.hub_entity)
        self.source = SftpImportSourceSatelliteFactory(
            upload_type=RECORDING_KEY,
            pipeline_parameters={"overwrite": True},
        )
        LinkSftpImportSourceSftpConnectionFactory(
            hub_in=self.source.hub_entity, hub_out=connection.hub_entity
        )
        self.fake_sftp = FakeTimedSftpClient(REMOTE_TREE)
        ssh_client_patcher = mock.patch(
            "sftp.managers.sftp_client_manager.paramiko.SSHClient"
        )
        self.ssh = ssh_client_patcher.start().return_value
        self.addCleanup(ssh_client_patcher.stop)
        self.ssh.open_sftp.return_value = self.fake_sftp
        RecordingFileUploadManager.calls = []

    def update_source(self, **fields) -> None:
        for field_name, value in fields.items():
            setattr(self.source, field_name, value)
        self.source.save()

    def sync(self, user_id: int | None = None):
        session_data = {"pk": self.source.hub_entity_id}
        if user_id is not None:
            session_data["user_id"] = user_id
        return SftpImportManager(session_data).sync()

    def get_source(self):
        return (
            SftpImportSourceRepository().receive().get(hub_id=self.source.hub_entity_id)
        )

    def imported_paths(self) -> list[str]:
        return sorted(
            SftpImportedFileRepository().receive().values_list("remote_path", flat=True)
        )


class TestSftpImportManagerSync(SftpImportManagerTestCase):
    def test_imports_accepted_files(self):
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv", "b.txt"])
        self.assertEqual(result.failed, [])
        self.assertEqual(result.status, PollStatus.SUCCESS)
        self.assertEqual(
            [call["name"] for call in RecordingFileUploadManager.calls],
            ["a.csv", "b.txt"],
        )
        self.assertEqual(RecordingFileUploadManager.calls[0]["content"], b"a,b\n1,2\n")

    def test_registers_files_in_upload_registry(self):
        self.sync(self.user.pk)
        registry = FileUploadRegistryRepository().receive()
        self.assertEqual(
            sorted(registry.values_list("file_name", flat=True)), ["a.csv", "b.txt"]
        )
        self.assertEqual(
            set(registry.values_list("upload_status", flat=True)), {"processed"}
        )

    def test_records_imported_files_in_ledger(self):
        self.sync(self.user.pk)
        self.assertEqual(self.imported_paths(), ["/upload/a.csv", "/upload/b.txt"])
        imported_file = (
            SftpImportedFileRepository().receive().get(remote_path="/upload/a.csv")
        )
        self.assertEqual(imported_file.file_size, len(b"a,b\n1,2\n"))
        self.assertEqual(imported_file.upload_type, RECORDING_KEY)
        self.assertEqual(
            imported_file.sftp_import_source_hub_id, self.source.hub_entity_id
        )
        registry = FileUploadRegistryRepository().receive().get(file_name="a.csv")
        self.assertEqual(imported_file.registry_hub_id, registry.hub_id)

    def test_moves_imported_files_to_processed_dir(self):
        self.sync(self.user.pk)
        upload_dir = self.fake_sftp.tree["upload"]
        self.assertEqual(sorted(upload_dir["processed"]), ["a.csv", "b.txt"])
        self.assertNotIn("a.csv", upload_dir)
        self.assertIn("c.pdf", upload_dir)

    def test_keeps_files_in_place_without_processed_dir(self):
        self.update_source(processed_dir="")
        self.sync(self.user.pk)
        upload_dir = self.fake_sftp.tree["upload"]
        self.assertNotIn("processed", upload_dir)
        self.assertIn("a.csv", upload_dir)

    def test_second_sync_imports_nothing(self):
        self.update_source(processed_dir="")
        self.sync(self.user.pk)
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, [])
        self.assertEqual(result.message, "No new files")
        self.assertEqual(len(RecordingFileUploadManager.calls), 2)

    def test_reimports_a_file_replaced_under_the_same_name(self):
        self.update_source(processed_dir="")
        self.sync(self.user.pk)
        self.fake_sftp.put_file("/upload/a.csv", b"a,b\n3,4\n5,6\n")
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv"])
        self.assertEqual(
            self.imported_paths(), ["/upload/a.csv", "/upload/a.csv", "/upload/b.txt"]
        )

    def test_archives_a_replaced_file_next_to_the_first(self):
        self.sync(self.user.pk)
        self.fake_sftp.put_file("/upload/a.csv", b"a,b\n3,4\n5,6\n")
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv"])
        upload_dir = self.fake_sftp.tree["upload"]
        self.assertNotIn("a.csv", upload_dir)
        self.assertEqual(upload_dir["processed"]["a.csv"], b"a,b\n1,2\n")
        self.assertEqual(upload_dir["processed"]["a_1.csv"], b"a,b\n3,4\n5,6\n")

    def test_moves_imported_file_left_behind(self):
        self.update_source(processed_dir="")
        self.sync(self.user.pk)
        self.update_source(processed_dir="processed")
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, [])
        self.assertEqual(
            sorted(self.fake_sftp.tree["upload"]["processed"]), ["a.csv", "b.txt"]
        )

    def test_applies_file_pattern(self):
        self.update_source(file_pattern="*.csv")
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv"])

    def test_skips_files_still_being_written(self):
        self.fake_sftp.put_file("/upload/new.csv", b"1", mtime=int(time.time()))
        result = self.sync(self.user.pk)
        self.assertNotIn("new.csv", result.imported)

    def test_polls_remote_dir(self):
        self.update_source(remote_dir="archive")
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["old.csv"])
        self.assertIn("processed", self.fake_sftp.tree["upload"]["archive"])

    def test_hands_pipeline_parameters_to_upload_manager(self):
        self.update_source(
            upload_type=f"{__name__}.RecordingWithDefaultsFileUploadManager"
        )
        self.sync(self.user.pk)
        call = RecordingFileUploadManager.calls[0]
        expected = {"overwrite": True, "sheet": "Data"}
        self.assertEqual(call["pipeline_data"], expected)
        self.assertEqual(call["session_data"]["user_id"], self.user.pk)
        self.assertEqual(call["session_data"]["overwrite"], True)
        self.assertEqual(call["session_data"]["sheet"], "Data")

    def test_pipeline_parameters_cannot_change_the_user(self):
        self.update_source(pipeline_parameters={"user_id": self.superuser.pk})
        self.sync(self.user.pk)
        call = RecordingFileUploadManager.calls[0]
        self.assertEqual(call["session_data"]["user_id"], self.user.pk)
        registry = FileUploadRegistryRepository().receive().first()
        self.assertEqual(registry.hub.created_by_id, self.user.pk)

    def test_runs_as_superuser_without_user(self):
        self.sync()
        call = RecordingFileUploadManager.calls[0]
        self.assertEqual(call["session_data"]["user_id"], self.superuser.pk)
        registry = FileUploadRegistryRepository().receive().first()
        self.assertEqual(registry.hub.created_by_id, self.superuser.pk)

    def test_async_pipeline(self):
        self.update_source(upload_type=TEST_UPLOAD_TYPE)
        result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv", "b.txt"])
        registry = FileUploadRegistryRepository().receive()
        self.assertEqual(registry.count(), 2)


class TestSftpImportManagerErrors(SftpImportManagerTestCase):
    def test_connection_error_is_recorded(self):
        self.ssh.connect.side_effect = paramiko.SSHException("Connection refused")
        result = self.sync(self.user.pk)
        self.assertEqual(result.status, PollStatus.FAILED)
        self.assertEqual(
            result.message, "Polling failed: SSHException: Connection refused"
        )
        source = self.get_source()
        self.assertEqual(source.last_poll_status, PollStatus.FAILED)
        self.assertEqual(source.last_poll_message, result.message)

    def test_missing_remote_dir_is_recorded(self):
        self.update_source(remote_dir="missing")
        result = self.sync(self.user.pk)
        self.assertEqual(result.status, PollStatus.FAILED)
        self.assertIn("FileNotFoundError", result.message)

    def test_unknown_upload_type_is_recorded(self):
        self.update_source(upload_type="gone.Manager")
        result = self.sync(self.user.pk)
        self.assertEqual(result.status, PollStatus.FAILED)
        self.assertIn("UnknownUnattendedUploadError", result.message)

    def test_pipeline_parameters_must_be_an_object(self):
        for parameters in (["overwrite"], "overwrite", 1):
            with self.subTest(parameters=parameters):
                self.update_source(pipeline_parameters=parameters)
                result = self.sync(self.user.pk)
                self.assertEqual(result.status, PollStatus.FAILED)
                self.assertIn("must be a JSON object", result.message)
                self.assertEqual(self.get_source().last_poll_message, result.message)
        self.assertEqual(RecordingFileUploadManager.calls, [])

    def test_failing_file_is_retried_next_time(self):
        with mock.patch.object(
            RecordingFileUploadManager,
            "upload_and_process",
            side_effect=ValueError("broken"),
        ):
            result = self.sync(self.user.pk)
        self.assertEqual(result.imported, [])
        self.assertEqual(len(result.failed), 2)
        self.assertEqual(result.status, PollStatus.FAILED)
        self.assertEqual(self.imported_paths(), [])
        self.assertIn("a.csv", self.fake_sftp.tree["upload"])
        self.assertEqual(self.sync(self.user.pk).imported, ["a.csv", "b.txt"])

    def test_failing_move_keeps_import(self):
        with mock.patch.object(
            FakeTimedSftpClient, "rename", side_effect=PermissionError("denied")
        ):
            result = self.sync(self.user.pk)
        self.assertEqual(result.imported, ["a.csv", "b.txt"])
        self.assertEqual(result.status, PollStatus.SUCCESS)
        self.assertEqual(self.imported_paths(), ["/upload/a.csv", "/upload/b.txt"])


class TestSftpImportManagerPollStatus(SftpImportManagerTestCase):
    def test_records_status(self):
        result = self.sync(self.user.pk)
        source = self.get_source()
        self.assertEqual(source.last_poll_status, PollStatus.SUCCESS)
        self.assertEqual(source.last_poll_message, result.message)
        self.assertIsNotNone(source.status_changed_at)
        # The settings are untouched by writing the status
        self.assertEqual(source.name, self.source.name)
        self.assertEqual(source.pipeline_parameters, {"overwrite": True})

    def test_writes_status_only_on_change(self):
        self.update_source(processed_dir="")
        self.sync(self.user.pk)
        self.sync(self.user.pk)
        changed_at = self.get_source().status_changed_at
        self.sync(self.user.pk)
        self.assertEqual(self.get_source().status_changed_at, changed_at)
        self.assertEqual(
            SftpImportSourceStatusSatellite.objects.filter(
                hub_entity_id=self.source.hub_entity_id
            ).count(),
            2,
        )
