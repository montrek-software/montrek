import datetime
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest import mock

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings
from django.utils import timezone

from storage.modules.local_storage_file import LocalStorageFile
from storage.modules.storage_cleanup import StorageCleanup

if TYPE_CHECKING:
    from django.test import SimpleTestCase

    _Base = SimpleTestCase
else:
    _Base = object


class StorageContractTests(_Base):
    """What montrek's storage code relies on from the default storage.

    Mix it into a test case of a storage backend, before the test case class,
    and return the backend's STORAGES["default"] entry from
    `default_storage_settings()`:

        class TestMyStorage(StorageContractTests, SimpleTestCase):
            def default_storage_settings(self):
                return {"BACKEND": "my_app.storage.MyStorage"}

    Each test works in a directory of its own, so the tests can share one
    container or bucket; the backend's test case removes what is left in it.
    Backend-specific behaviour, such as signed URLs, is tested there as well.
    """

    def default_storage_settings(self) -> dict[str, Any]:
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        override = override_settings(
            STORAGES={**settings.STORAGES, "default": self.default_storage_settings()}
        )
        override.enable()
        self.addCleanup(override.disable)
        self.directory = f"contract-{uuid.uuid4().hex}"

    def save(self, name: str, content: bytes = b"montrek") -> str:
        return default_storage.save(f"{self.directory}/{name}", ContentFile(content))

    def test_reads_back_what_it_stored(self):
        name = self.save("reports/q3.csv", b"a,b\n1,2\n")

        self.assertTrue(default_storage.exists(name))
        self.assertEqual(default_storage.size(name), 8)
        with default_storage.open(name, "rb") as stored:
            self.assertEqual(stored.read(), b"a,b\n1,2\n")

        default_storage.delete(name)
        self.assertFalse(default_storage.exists(name))

    def test_reads_back_a_file_of_several_megabytes(self):
        # Large enough that backends upload in chunks and spool downloads to a
        # temporary file.
        content = os.urandom(3 * 1024 * 1024)
        name = self.save("large.bin", content)
        with default_storage.open(name, "rb") as stored:
            self.assertEqual(stored.read(), content)

    def test_a_second_file_of_the_same_name_does_not_replace_the_first(self):
        first = self.save("upload.xlsx", b"first")
        second = self.save("upload.xlsx", b"second")

        self.assertNotEqual(first, second)
        with default_storage.open(first, "rb") as stored:
            self.assertEqual(stored.read(), b"first")

    def test_listdir_names_what_is_directly_under_a_directory(self):
        self.save("a/b/c.txt")
        self.save("a/d.txt")

        directories, files = default_storage.listdir(f"{self.directory}/a")
        self.assertEqual((sorted(directories), sorted(files)), (["b"], ["d.txt"]))

    def test_modified_time_is_timezone_aware(self):
        name = self.save("file.txt")
        modified = default_storage.get_modified_time(name)

        self.assertIsNotNone(modified.tzinfo)
        self.assertLess(abs(timezone.now() - modified), datetime.timedelta(minutes=1))

    def test_cleanup_deletes_only_old_files(self):
        name = self.save("old/file.csv")
        cleanup = StorageCleanup(self.directory, datetime.timedelta(days=7))

        self.assertEqual(cleanup.delete_old_files(), 0)
        later = timezone.now() + datetime.timedelta(days=8)
        with mock.patch(
            "storage.modules.storage_cleanup.timezone.now", return_value=later
        ):
            self.assertEqual(cleanup.delete_old_files(), 1)
        self.assertFalse(default_storage.exists(name))

    def test_cleanup_of_a_missing_directory_deletes_nothing(self):
        cleanup = StorageCleanup(f"{self.directory}/none", datetime.timedelta(days=7))
        self.assertEqual(cleanup.delete_old_files(), 0)

    def test_readers_that_need_a_path_get_one(self):
        name = self.save("imports/data.csv", b"x,y\n")

        with LocalStorageFile(name) as path:
            self.assertEqual(Path(path).name, Path(name).name)
            self.assertEqual(Path(path).read_bytes(), b"x,y\n")
