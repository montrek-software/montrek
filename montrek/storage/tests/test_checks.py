from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.test import SimpleTestCase, override_settings

from storage.checks import check_default_storage


class StorageWithoutItsSettings(FileSystemStorage):
    def __init__(self, **kwargs):
        raise ImproperlyConfigured("STORAGE_TEST_BUCKET is not set.")


class NotAStorage:
    pass


class TestCheckDefaultStorage(SimpleTestCase):
    def check(self, backend: str):
        with override_settings(
            STORAGES={**settings.STORAGES, "default": {"BACKEND": backend}}
        ):
            return check_default_storage()

    def test_a_storage_that_can_be_created_passes(self):
        self.assertEqual(self.check("django.core.files.storage.FileSystemStorage"), [])

    def test_a_backend_that_cannot_be_imported_is_an_error(self):
        (error,) = self.check("storage.no_such_module.Storage")
        self.assertEqual(error.id, "storage.E001")
        self.assertIn("storage.no_such_module.Storage", error.msg)

    def test_a_backend_missing_its_settings_is_an_error(self):
        (error,) = self.check(f"{__name__}.StorageWithoutItsSettings")
        self.assertEqual(error.id, "storage.E001")
        self.assertIn("STORAGE_TEST_BUCKET is not set.", error.msg)

    def test_a_class_that_is_no_storage_is_an_error(self):
        (error,) = self.check(f"{__name__}.NotAStorage")
        self.assertEqual(error.id, "storage.E002")

    def test_the_check_is_registered(self):
        from django.core.checks import registry

        self.assertIn(check_default_storage, registry.registry.get_checks())
