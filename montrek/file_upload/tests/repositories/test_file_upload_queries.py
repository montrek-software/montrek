from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from file_upload.repositories.file_upload_queries import (
    get_file_satellite_from_registry_satellite,
)
from file_upload.repositories.file_upload_queries import (
    get_account_hub_from_file_upload_registry_satellite,
)
from file_upload.repositories.file_upload_queries import new_file_upload_registry
from file_upload.repositories.file_upload_queries import new_file_upload_file
from file_upload.repositories.file_upload_queries import get_upload_regisrty_files_from_account_id
from file_upload.repositories.file_upload_queries import (
    get_file_satellite_from_registry_hub_id
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadFileStaticSatelliteFactory,
)
from account.tests.factories.account_factories import AccountHubFactory


class UploadTransactionToAccountFileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a file to upload
        txt_file_content = b"Test file content"
        cls.txt_file = SimpleUploadedFile("test_file.txt", txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory()
        cls.file_registry_sat_factory.hub_entity.link_file_upload_registry_file_upload_file.add(
            cls.file_file_sat_factory.hub_entity
        )
        cls.account_hub_factory = AccountHubFactory()
        cls.account_hub_factory.link_account_file_upload_registry.add(
            cls.file_registry_sat_factory.hub_entity
        )

    def tearDown(self):
        if default_storage.exists("uploads/test_file.txt"):
            default_storage.delete("uploads/test_file.txt")

    def test_get_file_satellite_from_registry_satellite(self):
        self.file_file_sat_factory.file = self.txt_file
        self.file_file_sat_factory.save()
        file_sat = get_file_satellite_from_registry_satellite(
            self.file_registry_sat_factory
        )
        self.assertEqual(file_sat.file.name, "uploads/test_file.txt")

    def test_get_account_hub_from_file_upload_registry_satellite(self):
        account_hub = get_account_hub_from_file_upload_registry_satellite(
            self.file_registry_sat_factory
        )
        self.assertEqual(account_hub, self.account_hub_factory)

    def test_new_file_upload_registry(self):
        file_registry_sat = new_file_upload_registry(
            self.account_hub_factory.id, self.txt_file
        )
        self.assertEqual(file_registry_sat.file_name, self.txt_file.name)
        self.assertEqual(file_registry_sat.upload_status, "pending")
        test_account = get_account_hub_from_file_upload_registry_satellite(
            file_registry_sat
        )
        self.assertEqual(test_account, self.account_hub_factory)

    def test_new_file_upload_file(self):
        file_file_sat = new_file_upload_file(
            self.file_registry_sat_factory, self.txt_file
        )
        self.assertEqual(file_file_sat.file.name, "uploads/test_file.txt")

    def test_get_upload_regisrty_files_from_account_id(self):
        test_upload_files = get_upload_regisrty_files_from_account_id(
            self.account_hub_factory.id
        )
        self.assertEqual(len(test_upload_files), 1)
        self.assertEqual(test_upload_files[0].file_name, self.txt_file.name)
        file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name="test_file2.txt"
        )
        self.account_hub_factory.link_account_file_upload_registry.add(
            file_registry_sat_factory.hub_entity
        )
        test_upload_files = get_upload_regisrty_files_from_account_id(
            self.account_hub_factory.id
        )
        self.assertEqual(len(test_upload_files), 2)
        self.assertEqual(test_upload_files[1].file_name, "test_file2.txt")

    def test_get_file_satellite_from_registry_hub_id(self):
        test_file_sat = get_file_satellite_from_registry_hub_id(
            self.file_registry_sat_factory.hub_entity.id
        )
        self.assertEqual(test_file_sat, self.file_file_sat_factory)
