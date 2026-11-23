"""Tests for STORAGE_BACKEND, which settings.py reads once per process.

Each test imports the settings in a new process with its own environment.
"""

import base64
import json
import os
import subprocess  # nosec B404
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# Any base64 value will do: signing a URL needs no connection to Azure.
ACCOUNT_KEY = base64.b64encode(b"\0" * 64).decode()

# Prints the default storage as the settings configure it, and a URL from it.
# Not default_storage: that is a lazy wrapper around it.
PROBE = """
import json
import django
django.setup()
from django.core.files.storage import storages
storage = storages["default"]
options = vars(storage)
print(json.dumps({
    "backend": type(storage).__module__ + "." + type(storage).__name__,
    "container": options.get("azure_container"),
    "credential": type(options.get("token_credential")).__name__,
    # With a managed identity, signing fetches a key from Azure first.
    "url": None if options.get("token_credential") else storage.url("reports/q3 final.pdf"),
}))
"""


class TestStorageBackend(SimpleTestCase):
    def probe(self, **environ):
        result = self.run_probe(**environ)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])

    def run_probe(self, **environ):
        environ = {
            **{k: v for k, v in os.environ.items() if not k.startswith("AZURE_")},
            "DJANGO_SETTINGS_MODULE": "montrek.settings",
            **environ,
        }
        return subprocess.run(  # noqa: S603  # nosec B603
            [sys.executable, "-c", PROBE],
            cwd=PROJECT_DIR,
            env=environ,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_the_filesystem_by_default(self):
        storage = self.probe(STORAGE_BACKEND="filesystem")
        self.assertEqual(
            storage["backend"], "django.core.files.storage.filesystem.FileSystemStorage"
        )
        self.assertEqual(storage["url"], "/uploads/reports/q3%20final.pdf")

    def test_azure_hands_out_short_lived_signed_urls(self):
        storage = self.probe(
            STORAGE_BACKEND="azure",
            AZURE_STORAGE_ACCOUNT_NAME="montrektest",
            AZURE_STORAGE_ACCOUNT_KEY=ACCOUNT_KEY,
            AZURE_STORAGE_URL_EXPIRATION_SECS="60",
        )
        self.assertEqual(
            storage["backend"], "storages.backends.azure_storage.AzureStorage"
        )
        self.assertEqual(storage["container"], "uploads")
        url = urlparse(storage["url"])
        self.assertEqual(url.netloc, "montrektest.blob.core.windows.net")
        self.assertEqual(url.path, "/uploads/reports/q3%20final.pdf")
        query = parse_qs(url.query)
        self.assertEqual(query["sp"], ["r"])
        self.assertIn("se", query)
        self.assertIn("sig", query)

    def test_azure_without_a_key_signs_in_as_the_managed_identity(self):
        storage = self.probe(
            STORAGE_BACKEND="azure",
            AZURE_STORAGE_ACCOUNT_NAME="montrektest",
            AZURE_STORAGE_CONTAINER="files",
        )
        self.assertEqual(storage["credential"], "DefaultAzureCredential")
        self.assertEqual(storage["container"], "files")

    def test_azure_with_a_connection_string_uses_its_endpoint(self):
        storage = self.probe(
            STORAGE_BACKEND="azure",
            AZURE_STORAGE_ACCOUNT_NAME="devstoreaccount1",
            AZURE_STORAGE_ACCOUNT_KEY=ACCOUNT_KEY,
            AZURE_STORAGE_CONNECTION_STRING=(
                "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
                f"AccountKey={ACCOUNT_KEY};"
                "BlobEndpoint=http://azurite:10000/devstoreaccount1;"
            ),
        )
        url = urlparse(storage["url"])
        self.assertEqual(url.netloc, "azurite:10000")
        self.assertEqual(url.path, "/devstoreaccount1/uploads/reports/q3%20final.pdf")
        self.assertIn("sig", parse_qs(url.query))

    def test_azure_needs_an_account_name(self):
        result = self.run_probe(STORAGE_BACKEND="azure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("needs AZURE_STORAGE_ACCOUNT_NAME", result.stderr)

    def test_an_unknown_backend_is_refused(self):
        result = self.run_probe(STORAGE_BACKEND="s3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STORAGE_BACKEND must be one of", result.stderr)
