from django.test import TestCase
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)

from info.models.download_registry_sat_models import DownloadType
from info.repositories.download_registry_repositories import DownloadRegistryRepository
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestDownloadRegistryMixin(TestCase):
    @add_logged_in_user()
    def test_write_to_registry(self):
        manager = DownloadRegistryStorageManager({"user_id": self.user.id})
        manager.store_in_download_registry(
            identifier="test_file", download_type=DownloadType.XLSX
        )
        repo = DownloadRegistryRepository()
        registry_element = repo.receive().get()
        self.assertEqual(registry_element.download_type, DownloadType.XLSX.value)
        self.assertEqual(registry_element.download_name, "test_file")
        self.assertEqual(registry_element.created_by, self.user.email)
        self.assertIsNotNone(registry_element.created_at)
