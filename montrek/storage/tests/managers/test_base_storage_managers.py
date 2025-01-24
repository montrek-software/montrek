from django.test import TestCase
from storage.managers.base_storage_managers import BaseStorageManager


class MockStorageManager(BaseStorageManager):
    def save(self, file_path: str):
        raise NotImplementedError

    def load(self) -> bytes:
        raise NotImplementedError


class TestMockStorageManager(TestCase):
    def test_save(self):
        with self.assertRaises(NotImplementedError):
            MockStorageManager().save("file_path")

    def test_load(self):
        with self.assertRaises(NotImplementedError):
            MockStorageManager().load()
