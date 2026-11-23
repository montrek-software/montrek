import tempfile

from django.test import SimpleTestCase, override_settings

from montrek.storage_settings import FILESYSTEM_BACKEND
from testing.test_cases.storage_contract_test_case import StorageContractTests


class TestFileSystemStorageContract(StorageContractTests, SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media_root = tempfile.TemporaryDirectory()
        cls.addClassCleanup(media_root.cleanup)
        override = override_settings(MEDIA_ROOT=media_root.name)
        override.enable()
        cls.addClassCleanup(override.disable)

    def default_storage_settings(self):
        return {"BACKEND": FILESYSTEM_BACKEND}


class TestObjectStorageContract(StorageContractTests, SimpleTestCase):
    """The stand-in the other tests use for an object storage."""

    def default_storage_settings(self):
        return {"BACKEND": "testing.decorators.object_storage.ObjectStorage"}
