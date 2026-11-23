import base64
from urllib.parse import parse_qs, urlparse

from azure.identity import DefaultAzureCredential
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import storages
from django.test import override_settings

from montrek.env_schema import CORE_SCHEMA_FILE, load_schema
from montrek.storage_settings import BACKENDS, StorageSettings
from montrek.tests.test_configuration import ConfigurationTestCase

# Any base64 value will do: signing a URL needs no connection to Azure.
ACCOUNT_KEY = base64.b64encode(b"\0" * 64).decode()

AZURE = {
    "STORAGE_BACKEND": "azure",
    "AZURE_STORAGE_ACCOUNT_NAME": "montrektest",
}
AZURE_WITH_KEY = {**AZURE, "AZURE_STORAGE_ACCOUNT_KEY": ACCOUNT_KEY}


class TestStorageSettings(ConfigurationTestCase):
    def default_storage(self, environ):
        return StorageSettings(self.build(environ)).default_storage()

    def url(self, default_storage, name="reports/q3 final.pdf"):
        """A URL from the storage that `default_storage` configures."""
        with override_settings(
            STORAGES={**settings.STORAGES, "default": default_storage}
        ):
            return urlparse(storages["default"].url(name))

    def test_the_filesystem_by_default(self):
        default_storage = self.default_storage({})
        self.assertEqual(
            default_storage,
            {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        )
        self.assertEqual(
            self.url(default_storage).path, "/uploads/reports/q3%20final.pdf"
        )

    def test_azure_hands_out_short_lived_signed_urls(self):
        default_storage = self.default_storage(
            {**AZURE_WITH_KEY, "AZURE_STORAGE_URL_EXPIRATION_SECS": "60"}
        )
        self.assertEqual(
            default_storage["BACKEND"], "storages.backends.azure_storage.AzureStorage"
        )
        self.assertEqual(default_storage["OPTIONS"]["azure_container"], "uploads")
        self.assertEqual(default_storage["OPTIONS"]["expiration_secs"], 60)
        url = self.url(default_storage)
        self.assertEqual(url.netloc, "montrektest.blob.core.windows.net")
        self.assertEqual(url.path, "/uploads/reports/q3%20final.pdf")
        query = parse_qs(url.query)
        self.assertEqual(query["sp"], ["r"])
        self.assertIn("se", query)
        self.assertIn("sig", query)

    def test_azure_without_a_key_signs_in_as_the_managed_identity(self):
        # No URL here: signing one fetches a user delegation key from Azure.
        options = self.default_storage({**AZURE, "AZURE_STORAGE_CONTAINER": "files"})[
            "OPTIONS"
        ]
        self.assertIsInstance(options["token_credential"], DefaultAzureCredential)
        self.assertNotIn("account_key", options)
        self.assertEqual(options["azure_container"], "files")

    def test_azure_with_a_connection_string_uses_its_endpoint(self):
        connection_string = (
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
            f"AccountKey={ACCOUNT_KEY};"
            "BlobEndpoint=http://azurite:10000/devstoreaccount1;"
        )
        url = self.url(
            self.default_storage(
                {
                    **AZURE_WITH_KEY,
                    "AZURE_STORAGE_ACCOUNT_NAME": "devstoreaccount1",
                    "AZURE_STORAGE_CONNECTION_STRING": connection_string,
                }
            )
        )
        self.assertEqual(url.netloc, "azurite:10000")
        self.assertEqual(url.path, "/devstoreaccount1/uploads/reports/q3%20final.pdf")
        self.assertIn("sig", parse_qs(url.query))

    def test_azure_needs_an_account_name(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "needs AZURE_STORAGE_ACCOUNT_NAME"
        ):
            self.default_storage({"STORAGE_BACKEND": "azure"})

    def test_azure_needs_a_positive_url_expiration(self):
        for value in ("0", "-60"):
            with self.subTest(value=value), self.assertRaisesMessage(
                ImproperlyConfigured,
                "AZURE_STORAGE_URL_EXPIRATION_SECS must be a positive number",
            ):
                self.default_storage(
                    {**AZURE_WITH_KEY, "AZURE_STORAGE_URL_EXPIRATION_SECS": value}
                )

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "STORAGE_BACKEND must be one of filesystem, azure"
        ):
            self.default_storage({"STORAGE_BACKEND": "s3"})

    def test_the_backends_match_the_schema(self):
        schema = load_schema(CORE_SCHEMA_FILE)
        self.assertEqual(schema["STORAGE_BACKEND"].choices, BACKENDS)
