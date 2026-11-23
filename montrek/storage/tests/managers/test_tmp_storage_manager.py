import os
import tempfile

from django.test import TestCase

from storage.managers.tmp_storage_manager import TmpStorageManager


class TestTmpStorageManager(TestCase):
    def test_save_and_cleanup(self):
        source = tempfile.TemporaryDirectory()
        self.addCleanup(source.cleanup)
        test_file_name = os.path.join(source.name, "test.txt")
        with open(test_file_name, "w") as f:
            f.write("test")
        tmp_storage_manager = TmpStorageManager()
        saved_path = tmp_storage_manager.save(test_file_name)
        self.assertTrue(os.path.exists(saved_path))
        tmp_storage_manager.cleanup()
        self.assertFalse(os.path.exists(saved_path))

    def test_save_file_not_found(self):
        tmp_storage_manager = TmpStorageManager()
        with self.assertRaises(FileNotFoundError):
            tmp_storage_manager.save("non_existent_file.txt")

    def test_load(self):
        tmp_storage_manager = TmpStorageManager()
        self.addCleanup(tmp_storage_manager.cleanup)
        with open(os.path.join(tmp_storage_manager.storage_path, "test.txt"), "w") as f:
            f.write("test")
        loaded_file = tmp_storage_manager.load("test.txt")
        self.assertEqual(loaded_file, b"test")

    def test_load_file_not_found(self):
        tmp_storage_manager = TmpStorageManager()
        with self.assertRaises(FileNotFoundError):
            tmp_storage_manager.load("non_existent_file.txt")
