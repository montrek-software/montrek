import datetime
import os
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.utils import timezone
from storage.modules.storage_cleanup import StorageCleanup
from testing.decorators.object_storage import object_storage

MAX_AGE = datetime.timedelta(days=7)


class TestStorageCleanup(TestCase):
    def setUp(self):
        # MEDIA_ROOT is shared by the whole test run.
        self.directory = f"cleanup/{self._testMethodName}"
        self.cleanup = StorageCleanup(self.directory, MAX_AGE)

    def _save_aged(self, name: str, age: datetime.timedelta) -> str:
        name = default_storage.save(name, ContentFile(b"x"))
        modified = (timezone.now() - age).timestamp()
        os.utime(default_storage.path(name), (modified, modified))
        return name

    def test_deletes_old_files_and_keeps_new_ones(self):
        old = self._save_aged(f"{self.directory}/a/old.csv", datetime.timedelta(days=8))
        new = self._save_aged(f"{self.directory}/b/new.csv", datetime.timedelta(days=1))

        self.assertEqual(self.cleanup.delete_old_files(), 1)

        self.assertFalse(default_storage.exists(old))
        self.assertTrue(default_storage.exists(new))

    def test_removes_the_directories_it_emptied(self):
        self._save_aged(f"{self.directory}/a/old.csv", datetime.timedelta(days=8))
        self._save_aged(f"{self.directory}/b/new.csv", datetime.timedelta(days=1))

        self.cleanup.delete_old_files()

        self.assertFalse(os.path.exists(default_storage.path(f"{self.directory}/a")))
        self.assertTrue(os.path.exists(default_storage.path(f"{self.directory}/b")))
        self.assertTrue(os.path.exists(default_storage.path(self.directory)))

    def test_missing_directory_deletes_nothing(self):
        self.assertEqual(
            StorageCleanup("cleanup_missing", MAX_AGE).delete_old_files(), 0
        )

    @object_storage
    def test_missing_prefix_on_object_storage_deletes_nothing(self):
        self.assertEqual(self.cleanup.delete_old_files(), 0)

    @object_storage
    def test_deletes_under_a_prefix_that_is_no_object(self):
        old = default_storage.save(f"{self.directory}/a/old.csv", ContentFile(b"x"))
        new = default_storage.save(f"{self.directory}/b/new.csv", ContentFile(b"x"))
        # As on S3, GCS or Azure Blob: the directory is a prefix, no object.
        self.assertFalse(default_storage.exists(self.directory))
        cutoff_passed = timezone.now() + datetime.timedelta(days=8)

        with mock.patch.object(timezone, "now", return_value=cutoff_passed):
            deleted = self.cleanup.delete_old_files()

        self.assertEqual(deleted, 2)
        self.assertFalse(default_storage.exists(old))
        self.assertFalse(default_storage.exists(new))
