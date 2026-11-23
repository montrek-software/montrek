from django.core.exceptions import ImproperlyConfigured

from montrek.storage_settings import FILESYSTEM_BACKEND, StorageSettings
from montrek.tests.test_configuration import ConfigurationTestCase


class TestStorageSettings(ConfigurationTestCase):
    def default_storage(self, environ):
        return StorageSettings(self.build(environ)).default_storage()

    def test_the_filesystem_by_default(self):
        for environ in ({}, {"STORAGE_BACKEND": "filesystem"}):
            with self.subTest(environ=environ):
                self.assertEqual(
                    self.default_storage(environ), {"BACKEND": FILESYSTEM_BACKEND}
                )

    def test_another_backend_by_its_dotted_path(self):
        backend = "montrek_example.storage.ExampleStorage"
        self.assertEqual(
            self.default_storage({"STORAGE_BACKEND": backend}), {"BACKEND": backend}
        )

    def test_a_value_that_is_no_dotted_path_is_refused(self):
        for value in ("azure", "", "storage.", "my-app.Storage", "a.b c"):
            with self.subTest(value=value), self.assertRaisesMessage(
                ImproperlyConfigured,
                "STORAGE_BACKEND must be filesystem or the dotted path of a "
                "storage class",
            ):
                self.default_storage({"STORAGE_BACKEND": value})
