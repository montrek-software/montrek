import os
from django.test import TestCase
from storage.managers.tmp_storage_manager import TmpStorageManager


class TestTmpStorageManager(TestCase):
    def test_save_and_cleanup(self):
        test_file_name = "test.txt"
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
        pass
