"""The storage code against real Blob Storage, as the Azurite emulator serves it.

The other storage tests use an in-memory stand-in; these check that the Azure
backend behaves the way the code relies on. They need Azurite:

    docker run --rm -p 127.0.0.1:10000:10000 \
        mcr.microsoft.com/azure-storage/azurite:3.38.0 \
        azurite-blob --blobHost 0.0.0.0

Without it they are skipped, unless AZURITE_BLOB_URL is set (as in CI): then a
missing Azurite is a failure, not a skip.
"""

import datetime
import os
import socket
import uuid
from pathlib import Path
from unittest import SkipTest, mock
from urllib.parse import urlparse, urlunparse

import requests
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings, tag
from django.utils import timezone

from montrek.storage_settings import StorageSettings
from montrek.testing.test_runner import real_socket
from montrek.tests.test_configuration import ConfigurationTestCase
from storage.modules.local_storage_file import LocalStorageFile
from storage.modules.storage_cleanup import StorageCleanup

ACCOUNT_NAME = "devstoreaccount1"
# Azurite's built-in key, the same in every installation and published in its
# documentation: it guards nothing.
ACCOUNT_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="  # gitleaks:allow
BLOB_URL = os.environ.get("AZURITE_BLOB_URL", f"http://127.0.0.1:10000/{ACCOUNT_NAME}")
CONNECTION_STRING = (
    f"DefaultEndpointsProtocol=http;AccountName={ACCOUNT_NAME};"
    f"AccountKey={ACCOUNT_KEY};BlobEndpoint={BLOB_URL};"
)


def azurite_reachable() -> bool:
    url = urlparse(BLOB_URL)
    try:
        with socket.create_connection((url.hostname, url.port or 80), timeout=1):
            return True
    except OSError:
        return False


@tag("azurite")
class TestAzureBlobStorage(ConfigurationTestCase):
    @classmethod
    def setUpClass(cls):
        # The test runner forbids network access; these tests need it, to
        # Azurite only. Restored even when the class is skipped or fails here.
        cls.addClassCleanup(setattr, socket, "socket", socket.socket)
        socket.socket = real_socket
        if not azurite_reachable():
            if "AZURITE_BLOB_URL" in os.environ:
                raise RuntimeError(f"No Azurite at AZURITE_BLOB_URL={BLOB_URL}.")
            raise SkipTest(f"No Azurite at {BLOB_URL}.")
        super().setUpClass()
        # One container per run, so parallel runs do not see each other's files.
        cls.container = f"montrek-test-{uuid.uuid4().hex}"
        cls.service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        cls.service.create_container(cls.container)
        cls.addClassCleanup(cls.service.delete_container, cls.container)

    def setUp(self):
        super().setUp()
        config = self.build(
            {
                "STORAGE_BACKEND": "azure",
                "AZURE_STORAGE_ACCOUNT_NAME": ACCOUNT_NAME,
                "AZURE_STORAGE_ACCOUNT_KEY": ACCOUNT_KEY,
                "AZURE_STORAGE_CONNECTION_STRING": CONNECTION_STRING,
                "AZURE_STORAGE_CONTAINER": self.container,
            }
        )
        storages = {
            **settings.STORAGES,
            "default": StorageSettings(config).default_storage(),
        }
        override = override_settings(STORAGES=storages)
        override.enable()
        self.addCleanup(override.disable)
        # Under its own prefix, so the tests do not see each other's files.
        self.directory = self._testMethodName

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

    def test_reads_back_a_file_larger_than_its_memory_buffer(self):
        # Above the backend's 2 MB, uploads are chunked and downloads spooled
        # to a temporary file.
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

    def test_a_directory_is_only_a_prefix(self):
        self.save("a/b/c.txt")
        self.save("a/d.txt")

        self.assertFalse(default_storage.exists(f"{self.directory}/a"))
        self.assertEqual(
            default_storage.listdir(f"{self.directory}/a"), (["b"], ["d.txt"])
        )

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

    def test_readers_that_need_a_path_get_a_temporary_copy(self):
        name = self.save("imports/data.csv", b"x,y\n")

        with LocalStorageFile(name) as path:
            self.assertEqual(Path(path).name, "data.csv")
            self.assertEqual(Path(path).read_bytes(), b"x,y\n")
        self.assertFalse(Path(path).exists())

    def test_a_signed_url_delivers_the_file(self):
        name = self.save("reports/q3.pdf", b"%PDF-1.7")
        url = default_storage.url(name)

        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"%PDF-1.7")
        self.assertEqual(response.headers["Content-Type"], "application/pdf")

    def test_the_container_refuses_a_url_without_a_valid_signature(self):
        name = self.save("reports/q3.pdf", b"%PDF-1.7")
        unsigned = urlunparse(urlparse(default_storage.url(name))._replace(query=""))
        expired = default_storage.url(name, expire=-60)

        for url in (unsigned, expired):
            with self.subTest(url=url):
                response = requests.get(url, timeout=10)
                self.assertNotEqual(response.status_code, 200)
                self.assertNotEqual(response.content, b"%PDF-1.7")
