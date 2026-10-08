"""The A1 upload fed from an SFTP folder instead of the upload form.

A1FileUploadManager opts in with allow_unattended_upload, so an SFTP import
source can name it as its upload type. This runs a whole poll against an
in-memory SFTP server: the CSV dropped there ends up as HubA rows, in the A1
upload registry and in the source's ledger, and is moved to "processed".
"""

from unittest import mock

from django.test import TransactionTestCase

from montrek_example.repositories.hub_a_repository import (
    HubAFileUploadRegistryRepository,
    HubARepository,
)
from montrek_example.tests.factories import montrek_example_factories as me_factories
from sftp.managers.sftp_import_manager import SftpImportManager
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportedFileRepository,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
)
from sftp.tests.factories.sftp_import_source_factories import (
    LinkSftpImportSourceSftpConnectionFactory,
    SftpImportSourceSatelliteFactory,
)
from sftp.tests.managers.test_sftp_client_manager import FakeSftpClient
from user.tests.factories.montrek_user_factories import MontrekUserFactory

# As montrek_example/tests/data/a_file.csv
A_FILE_CONTENT = (
    b"source_field_0,source_field_1,source_field_2,source_field_3\n"
    b"a,1,0,2021\n"
    b"b,2,5,2022\n"
    b"c,3,6,2023\n"
)


class TestA1SftpImport(TransactionTestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        # The A1 field map: which CSV column fills which HubA field
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_str",
            function_name="append_source_field_1",
        )
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_1",
            database_field="field_a1_int",
            function_name="multiply_by_value",
            function_parameters={"value": 1000},
        )
        connection = SftpConnectionSatelliteFactory(base_path="/outbox")
        SftpCredentialSatelliteFactory(hub_entity=connection.hub_entity)
        self.source = SftpImportSourceSatelliteFactory(
            name="A1 from partner",
            remote_dir="a1",
            file_pattern="a_*.csv",
            upload_type=(
                "montrek_example.managers.a1_file_upload_manager.A1FileUploadManager"
            ),
            processed_dir="processed",
        )
        LinkSftpImportSourceSftpConnectionFactory(
            hub_in=self.source.hub_entity, hub_out=connection.hub_entity
        )
        self.fake_sftp = FakeSftpClient(
            {
                "outbox": {
                    "a1": {
                        "a_file.csv": A_FILE_CONTENT,
                        "readme.txt": b"not matched by the pattern",
                    }
                }
            }
        )
        patcher = mock.patch("sftp.managers.sftp_client_manager.paramiko.SSHClient")
        patcher.start().return_value.open_sftp.return_value = self.fake_sftp
        self.addCleanup(patcher.stop)

    def sync(self):
        return SftpImportManager(
            {"pk": self.source.hub_entity_id, "user_id": self.user.pk}
        ).sync()

    def test_imports_csv_into_hub_a(self):
        result = self.sync()
        self.assertEqual(result.imported, ["a_file.csv"])
        a_hubs = HubARepository().receive()
        self.assertEqual(
            [(a.field_a1_str, a.field_a1_int) for a in a_hubs],
            [("a1", 1000), ("b2", 2000), ("c3", 3000)],
        )

    def test_registers_upload_in_a1_registry(self):
        self.sync()
        registry = HubAFileUploadRegistryRepository({}).receive().get()
        self.assertEqual(registry.file_name, "a_file.csv")
        self.assertEqual(registry.upload_status, "processed")
        imported_file = SftpImportedFileRepository().receive().get()
        self.assertEqual(imported_file.remote_path, "/outbox/a1/a_file.csv")
        self.assertEqual(imported_file.registry_hub_id, registry.hub_id)

    def test_moves_file_to_processed_and_imports_once(self):
        self.sync()
        a1_dir = self.fake_sftp.tree["outbox"]["a1"]
        self.assertEqual(list(a1_dir["processed"]), ["a_file.csv"])
        self.assertIn("readme.txt", a1_dir)
        self.assertEqual(self.sync().message, "No new files")
        self.assertEqual(HubARepository().receive().count(), 3)
