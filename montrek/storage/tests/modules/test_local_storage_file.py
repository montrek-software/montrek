from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from storage.modules.local_storage_file import LocalStorageFile
from testing.decorators.object_storage import object_storage


class TestLocalStorageFile(TestCase):
    def test_filesystem_storage_hands_out_the_stored_file(self):
        name = default_storage.save("local_files/data.csv", ContentFile(b"a,b"))
        with LocalStorageFile(name) as path:
            self.assertEqual(path, default_storage.path(name))
        self.assertTrue(default_storage.exists(name))

    @object_storage
    def test_other_storages_get_a_copy_with_the_file_name_removed_afterwards(self):
        name = default_storage.save("local_files/data.csv", ContentFile(b"a,b"))
        with LocalStorageFile(name) as path:
            self.assertEqual(Path(path).name, "data.csv")
            self.assertEqual(Path(path).read_bytes(), b"a,b")
        self.assertFalse(Path(path).exists())
        self.assertTrue(default_storage.exists(name))
